import httpx
import pytest

from norway_job_market_intelligence.config import NavFeedSettings
from norway_job_market_intelligence.ingestion.exceptions import (
    NavFeedAuthenticationError,
    NavFeedConfigurationError,
    NavFeedInvalidJsonError,
    NavFeedRequestError,
    NavFeedStructureError,
)
from norway_job_market_intelligence.ingestion.nav_client import NavFeedClient

FEED_URL = "https://feed.example.test/api/v1/feed"
TOKEN = "fictional-nav-token"


def test_fetch_feed_page_returns_structured_result() -> None:
    captured_request: httpx.Request | None = None

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal captured_request
        captured_request = request

        return httpx.Response(
            200,
            json={
                "items": [
                    {
                        "id": "event-1",
                        "type": "CREATE",
                    },
                    {
                        "id": "event-2",
                        "type": "UPDATE",
                    },
                ],
                "next_url": "/api/v1/feed?page=2",
            },
            headers={
                "ETag": '"current-etag"',
                "Last-Modified": "Wed, 29 Jul 2026 08:00:00 GMT",
            },
        )

    settings = NavFeedSettings(
        token=TOKEN,
        feed_url=FEED_URL,
        timeout_seconds=10,
        user_agent="njmi-tests/1.0",
    )

    with NavFeedClient(
        settings,
        transport=httpx.MockTransport(handler),
    ) as client:
        result = client.fetch_feed_page(
            etag='"previous-etag"',
            last_modified="Tue, 28 Jul 2026 08:00:00 GMT",
        )

    assert captured_request is not None
    assert str(captured_request.url) == FEED_URL
    assert captured_request.headers["Authorization"] == f"Bearer {TOKEN}"
    assert captured_request.headers["Accept"] == "application/json"
    assert captured_request.headers["User-Agent"] == "njmi-tests/1.0"
    assert captured_request.headers["If-None-Match"] == '"previous-etag"'
    assert captured_request.headers["If-Modified-Since"] == "Tue, 28 Jul 2026 08:00:00 GMT"

    assert result.request_url == FEED_URL
    assert result.status_code == 200
    assert result.payload == {
        "items": [
            {
                "id": "event-1",
                "type": "CREATE",
            },
            {
                "id": "event-2",
                "type": "UPDATE",
            },
        ],
        "next_url": "/api/v1/feed?page=2",
    }
    assert result.items == (
        {
            "id": "event-1",
            "type": "CREATE",
        },
        {
            "id": "event-2",
            "type": "UPDATE",
        },
    )
    assert result.next_url == "https://feed.example.test/api/v1/feed?page=2"
    assert result.etag == '"current-etag"'
    assert result.last_modified == "Wed, 29 Jul 2026 08:00:00 GMT"
    assert result.not_modified is False


def test_fetch_feed_page_accepts_same_origin_relative_page_url() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert str(request.url) == ("https://feed.example.test/api/v1/feed?page=2")
        return httpx.Response(
            200,
            json={
                "items": [],
                "next_url": None,
            },
        )

    settings = NavFeedSettings(
        token=TOKEN,
        feed_url=FEED_URL,
    )

    with NavFeedClient(
        settings,
        transport=httpx.MockTransport(handler),
    ) as client:
        result = client.fetch_feed_page("?page=2")

    assert result.status_code == 200
    assert result.items == ()
    assert result.next_url is None


def test_not_modified_response_does_not_require_json_body() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            304,
            content=b"not-json",
            headers={
                "ETag": '"unchanged-etag"',
                "Last-Modified": "Wed, 29 Jul 2026 08:00:00 GMT",
            },
        )

    settings = NavFeedSettings(
        token=TOKEN,
        feed_url=FEED_URL,
    )

    with NavFeedClient(
        settings,
        transport=httpx.MockTransport(handler),
    ) as client:
        result = client.fetch_feed_page()

    assert result.status_code == 304
    assert result.payload is None
    assert result.items == ()
    assert result.next_url is None
    assert result.etag == '"unchanged-etag"'
    assert result.last_modified == "Wed, 29 Jul 2026 08:00:00 GMT"
    assert result.not_modified is True


@pytest.mark.parametrize("status_code", [401, 403])
def test_authentication_failure_raises_safe_error(
    status_code: int,
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            status_code,
            text=f"Rejected token: {TOKEN}",
        )

    settings = NavFeedSettings(
        token=TOKEN,
        feed_url=FEED_URL,
    )

    with (
        NavFeedClient(
            settings,
            transport=httpx.MockTransport(handler),
        ) as client,
        pytest.raises(
            NavFeedAuthenticationError,
            match="authentication or authorization was rejected",
        ) as captured_error,
    ):
        client.fetch_feed_page()

    assert TOKEN not in str(captured_error.value)


def test_non_success_status_raises_request_error_without_body() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            500,
            text=f"Internal failure containing {TOKEN}",
        )

    settings = NavFeedSettings(
        token=TOKEN,
        feed_url=FEED_URL,
    )

    with (
        NavFeedClient(
            settings,
            transport=httpx.MockTransport(handler),
        ) as client,
        pytest.raises(
            NavFeedRequestError,
            match="HTTP status 500",
        ) as captured_error,
    ):
        client.fetch_feed_page()

    assert TOKEN not in str(captured_error.value)
    assert "Internal failure" not in str(captured_error.value)


def test_redirect_response_is_not_followed() -> None:
    request_count = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal request_count
        request_count += 1

        return httpx.Response(
            302,
            headers={
                "Location": "https://external.example.test/feed",
            },
        )

    settings = NavFeedSettings(
        token=TOKEN,
        feed_url=FEED_URL,
    )

    with (
        NavFeedClient(
            settings,
            transport=httpx.MockTransport(handler),
        ) as client,
        pytest.raises(
            NavFeedRequestError,
            match="HTTP status 302",
        ),
    ):
        client.fetch_feed_page()

    assert request_count == 1


def test_invalid_json_raises_response_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            content=b"{invalid-json",
            headers={"Content-Type": "application/json"},
        )

    settings = NavFeedSettings(
        token=TOKEN,
        feed_url=FEED_URL,
    )

    with (
        NavFeedClient(
            settings,
            transport=httpx.MockTransport(handler),
        ) as client,
        pytest.raises(
            NavFeedInvalidJsonError,
            match="did not contain valid JSON",
        ),
    ):
        client.fetch_feed_page()


def test_non_object_json_response_is_rejected() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json=[],
        )

    settings = NavFeedSettings(
        token=TOKEN,
        feed_url=FEED_URL,
    )

    with (
        NavFeedClient(
            settings,
            transport=httpx.MockTransport(handler),
        ) as client,
        pytest.raises(
            NavFeedStructureError,
            match="must contain a JSON object",
        ),
    ):
        client.fetch_feed_page()


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"items": None},
        {"items": {}},
    ],
)
def test_missing_or_invalid_items_array_is_rejected(
    payload: dict[str, object],
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json=payload,
        )

    settings = NavFeedSettings(
        token=TOKEN,
        feed_url=FEED_URL,
    )

    with (
        NavFeedClient(
            settings,
            transport=httpx.MockTransport(handler),
        ) as client,
        pytest.raises(
            NavFeedStructureError,
            match="must contain an items array",
        ),
    ):
        client.fetch_feed_page()


def test_non_object_feed_item_is_rejected() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "items": ["invalid-item"],
                "next_url": None,
            },
        )

    settings = NavFeedSettings(
        token=TOKEN,
        feed_url=FEED_URL,
    )

    with (
        NavFeedClient(
            settings,
            transport=httpx.MockTransport(handler),
        ) as client,
        pytest.raises(
            NavFeedStructureError,
            match="Every NAV feed item must be a JSON object",
        ),
    ):
        client.fetch_feed_page()


@pytest.mark.parametrize(
    "next_url",
    ["", "   ", 42, []],
)
def test_invalid_next_url_is_rejected(next_url: object) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "items": [],
                "next_url": next_url,
            },
        )

    settings = NavFeedSettings(
        token=TOKEN,
        feed_url=FEED_URL,
    )

    with (
        NavFeedClient(
            settings,
            transport=httpx.MockTransport(handler),
        ) as client,
        pytest.raises(
            NavFeedStructureError,
            match="next_url must be a non-empty string or null",
        ),
    ):
        client.fetch_feed_page()


def test_cross_origin_page_url_is_rejected_before_request() -> None:
    request_was_sent = False

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal request_was_sent
        request_was_sent = True
        return httpx.Response(200, json={"items": []})

    settings = NavFeedSettings(
        token=TOKEN,
        feed_url=FEED_URL,
    )

    with (
        NavFeedClient(
            settings,
            transport=httpx.MockTransport(handler),
        ) as client,
        pytest.raises(
            NavFeedStructureError,
            match="must use the configured feed origin",
        ),
    ):
        client.fetch_feed_page("https://external.example.test/api/v1/feed?page=2")

    assert request_was_sent is False


@pytest.mark.parametrize(
    "feed_url",
    [
        "not-a-url",
        "ftp://feed.example.test/api/v1/feed",
        "https://user:password@feed.example.test/api/v1/feed",
        "https://feed.example.test/api/v1/feed#fragment",
    ],
)
def test_invalid_configured_feed_url_is_rejected(
    feed_url: str,
) -> None:
    settings = NavFeedSettings(
        token=TOKEN,
        feed_url=feed_url,
    )

    with (
        NavFeedClient(
            settings,
            transport=httpx.MockTransport(lambda request: httpx.Response(200)),
        ) as client,
        pytest.raises(
            NavFeedConfigurationError,
            match="NAV_FEED_URL must be an absolute HTTP",
        ),
    ):
        client.fetch_feed_page()


def test_missing_token_prevents_http_request() -> None:
    request_was_sent = False

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal request_was_sent
        request_was_sent = True
        return httpx.Response(200, json={"items": []})

    settings = NavFeedSettings(
        token=None,
        feed_url=FEED_URL,
    )

    with (
        NavFeedClient(
            settings,
            transport=httpx.MockTransport(handler),
        ) as client,
        pytest.raises(
            NavFeedConfigurationError,
            match="NAV_FEED_TOKEN is required",
        ),
    ):
        client.fetch_feed_page()

    assert request_was_sent is False


def test_timeout_is_translated_to_safe_request_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout(
            f"Timeout containing {TOKEN}",
            request=request,
        )

    settings = NavFeedSettings(
        token=TOKEN,
        feed_url=FEED_URL,
    )

    with (
        NavFeedClient(
            settings,
            transport=httpx.MockTransport(handler),
        ) as client,
        pytest.raises(
            NavFeedRequestError,
            match="request timed out",
        ) as captured_error,
    ):
        client.fetch_feed_page()

    assert TOKEN not in str(captured_error.value)


def test_transport_error_is_translated_to_safe_request_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError(
            f"Connection failure containing {TOKEN}",
            request=request,
        )

    settings = NavFeedSettings(
        token=TOKEN,
        feed_url=FEED_URL,
    )

    with (
        NavFeedClient(
            settings,
            transport=httpx.MockTransport(handler),
        ) as client,
        pytest.raises(
            NavFeedRequestError,
            match="could not be completed",
        ) as captured_error,
    ):
        client.fetch_feed_page()

    assert TOKEN not in str(captured_error.value)


def test_cross_origin_next_url_in_response_is_rejected() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "items": [],
                "next_url": "https://external.example.test/feed?page=2",
            },
        )

    settings = NavFeedSettings(
        token=TOKEN,
        feed_url=FEED_URL,
    )

    with (
        NavFeedClient(
            settings,
            transport=httpx.MockTransport(handler),
        ) as client,
        pytest.raises(
            NavFeedStructureError,
            match="next_url must use the response origin",
        ),
    ):
        client.fetch_feed_page()
