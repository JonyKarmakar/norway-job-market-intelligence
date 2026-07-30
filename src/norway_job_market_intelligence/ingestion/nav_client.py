"""HTTP client for retrieving individual NAV vacancy-feed pages."""

from dataclasses import dataclass
from typing import cast
from urllib.parse import urljoin, urlsplit

import httpx

from norway_job_market_intelligence.config import NavFeedSettings
from norway_job_market_intelligence.ingestion.exceptions import (
    NavFeedAuthenticationError,
    NavFeedConfigurationError,
    NavFeedInvalidJsonError,
    NavFeedRequestError,
    NavFeedStructureError,
)


@dataclass(frozen=True, slots=True)
class NavFeedPageResult:
    """Structured result returned after requesting one NAV feed page."""

    request_url: str
    status_code: int
    payload: dict[str, object] | None
    items: tuple[dict[str, object], ...]
    next_url: str | None
    etag: str | None
    last_modified: str | None
    not_modified: bool


class NavFeedClient:
    """Synchronous client responsible for fetching one feed page at a time."""

    def __init__(
        self,
        settings: NavFeedSettings,
        *,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self._settings = settings
        self._client = httpx.Client(
            timeout=settings.timeout_seconds,
            transport=transport,
            follow_redirects=False,
        )

    def __enter__(self) -> "NavFeedClient":
        return self

    def __exit__(
        self,
        exception_type: object,
        exception: object,
        traceback: object,
    ) -> None:
        self.close()

    def close(self) -> None:
        """Release HTTP client resources."""

        self._client.close()

    def fetch_feed_page(
        self,
        page_url: str | None = None,
        *,
        etag: str | None = None,
        last_modified: str | None = None,
    ) -> NavFeedPageResult:
        """Fetch and validate one NAV vacancy-feed page."""

        request_url = self._resolve_request_url(page_url)
        headers = self._build_headers(
            etag=etag,
            last_modified=last_modified,
        )

        try:
            response = self._client.get(
                request_url,
                headers=headers,
            )
        except httpx.TimeoutException:
            raise NavFeedRequestError("NAV feed request timed out.") from None
        except (httpx.RequestError, httpx.InvalidURL):
            raise NavFeedRequestError("NAV feed request could not be completed.") from None

        response_etag = response.headers.get("ETag")
        response_last_modified = response.headers.get("Last-Modified")

        if response.status_code == 304:
            return NavFeedPageResult(
                request_url=str(response.url),
                status_code=response.status_code,
                payload=None,
                items=(),
                next_url=None,
                etag=response_etag,
                last_modified=response_last_modified,
                not_modified=True,
            )

        if response.status_code in {401, 403}:
            raise NavFeedAuthenticationError(
                "NAV feed authentication or authorization was rejected."
            )

        if not 200 <= response.status_code < 300:
            raise NavFeedRequestError(
                f"NAV feed request failed with HTTP status {response.status_code}."
            )

        page_payload = self._decode_page_payload(response)
        items = self._extract_items(page_payload)
        next_url = self._extract_next_url(
            page_payload,
            response_url=str(response.url),
        )

        return NavFeedPageResult(
            request_url=str(response.url),
            status_code=response.status_code,
            payload=page_payload,
            items=items,
            next_url=next_url,
            etag=response_etag,
            last_modified=response_last_modified,
            not_modified=False,
        )

    def _resolve_request_url(self, page_url: str | None) -> str:
        base_url = self._settings.feed_url.strip()
        base_parts = urlsplit(base_url)

        if (
            base_parts.scheme.lower() not in {"http", "https"}
            or not base_parts.netloc
            or base_parts.username is not None
            or base_parts.password is not None
            or bool(base_parts.fragment)
        ):
            raise NavFeedConfigurationError(
                "NAV_FEED_URL must be an absolute HTTP(S) URL without "
                "embedded credentials or a fragment."
            )

        if page_url is None:
            return base_url

        normalized_page_url = page_url.strip()

        if not normalized_page_url:
            raise NavFeedStructureError("NAV feed page URL must not be empty.")

        resolved_url = urljoin(base_url, normalized_page_url)
        resolved_parts = urlsplit(resolved_url)

        if (
            resolved_parts.scheme.lower() not in {"http", "https"}
            or not resolved_parts.netloc
            or resolved_parts.username is not None
            or resolved_parts.password is not None
            or bool(resolved_parts.fragment)
        ):
            raise NavFeedStructureError(
                "NAV feed page URL must be an absolute HTTP(S) URL without "
                "embedded credentials or a fragment."
            )

        base_origin = (
            base_parts.scheme.lower(),
            base_parts.netloc.lower(),
        )
        resolved_origin = (
            resolved_parts.scheme.lower(),
            resolved_parts.netloc.lower(),
        )

        if resolved_origin != base_origin:
            raise NavFeedStructureError("NAV feed page URL must use the configured feed origin.")

        return resolved_url

    def _build_headers(
        self,
        *,
        etag: str | None,
        last_modified: str | None,
    ) -> dict[str, str]:
        token = self._settings.require_token()

        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {token}",
            "User-Agent": self._settings.user_agent,
        }

        if etag:
            headers["If-None-Match"] = etag

        if last_modified:
            headers["If-Modified-Since"] = last_modified

        return headers

    @staticmethod
    def _decode_page_payload(
        response: httpx.Response,
    ) -> dict[str, object]:
        try:
            raw_payload: object = response.json()
        except ValueError:
            raise NavFeedInvalidJsonError("NAV feed response did not contain valid JSON.") from None

        if not isinstance(raw_payload, dict):
            raise NavFeedStructureError("NAV feed response must contain a JSON object.")

        if not all(isinstance(key, str) for key in raw_payload):
            raise NavFeedStructureError("NAV feed response object keys must be strings.")

        return cast(dict[str, object], raw_payload)

    @staticmethod
    def _extract_items(
        page_payload: dict[str, object],
    ) -> tuple[dict[str, object], ...]:
        raw_items = page_payload.get("items")

        if not isinstance(raw_items, list):
            raise NavFeedStructureError("NAV feed response must contain an items array.")

        items: list[dict[str, object]] = []

        for raw_item in raw_items:
            if not isinstance(raw_item, dict):
                raise NavFeedStructureError("Every NAV feed item must be a JSON object.")

            if not all(isinstance(key, str) for key in raw_item):
                raise NavFeedStructureError("NAV feed item object keys must be strings.")

            items.append(cast(dict[str, object], raw_item))

        return tuple(items)

    @staticmethod
    def _extract_next_url(
        page_payload: dict[str, object],
        *,
        response_url: str,
    ) -> str | None:
        raw_next_url = page_payload.get("next_url")

        if raw_next_url is None:
            return None

        if not isinstance(raw_next_url, str) or not raw_next_url.strip():
            raise NavFeedStructureError("NAV feed next_url must be a non-empty string or null.")

        resolved_next_url = urljoin(response_url, raw_next_url)
        response_parts = urlsplit(response_url)
        next_parts = urlsplit(resolved_next_url)

        if (
            next_parts.scheme.lower() not in {"http", "https"}
            or not next_parts.netloc
            or next_parts.username is not None
            or next_parts.password is not None
            or bool(next_parts.fragment)
        ):
            raise NavFeedStructureError(
                "NAV feed next_url must be an absolute HTTP(S) URL without "
                "embedded credentials or a fragment."
            )

        response_origin = (
            response_parts.scheme.lower(),
            response_parts.netloc.lower(),
        )
        next_origin = (
            next_parts.scheme.lower(),
            next_parts.netloc.lower(),
        )

        if next_origin != response_origin:
            raise NavFeedStructureError("NAV feed next_url must use the response origin.")

        return resolved_next_url
