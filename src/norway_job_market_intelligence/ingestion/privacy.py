"""Privacy-safe processing for NAV advertisement payloads."""

import hashlib
import json
from copy import deepcopy
from dataclasses import dataclass
from typing import cast

from norway_job_market_intelligence.ingestion.exceptions import (
    PrivacyValidationError,
)


@dataclass(frozen=True, slots=True)
class PreparedNavPayload:
    """Privacy-minimised payload and its deterministic SHA-256 hash."""

    payload: dict[str, object]
    payload_hash: str


def minimise_payload(payload: object) -> dict[str, object]:
    """Return a privacy-minimised copy of a NAV payload."""

    source_payload = _require_json_object(payload)
    minimised_payload = deepcopy(source_payload)
    minimised_payload.pop("contactList", None)

    validate_minimised_payload(minimised_payload)
    return minimised_payload


def validate_minimised_payload(payload: object) -> None:
    """Validate that a payload satisfies the persistent privacy boundary."""

    payload_object = _require_json_object(payload)

    if "contactList" in payload_object:
        raise PrivacyValidationError("Privacy-minimised NAV payload must not contain contactList.")

    _canonical_json(payload_object)


def calculate_payload_hash(payload: object) -> str:
    """Calculate a deterministic SHA-256 hash for a minimised payload."""

    payload_object = _require_json_object(payload)
    validate_minimised_payload(payload_object)

    canonical_payload = _canonical_json(payload_object)
    return hashlib.sha256(canonical_payload.encode("utf-8")).hexdigest()


def prepare_payload(payload: object) -> PreparedNavPayload:
    """Minimise, validate and hash one NAV payload in the required order."""

    minimised_payload = minimise_payload(payload)

    return PreparedNavPayload(
        payload=minimised_payload,
        payload_hash=calculate_payload_hash(minimised_payload),
    )


def _require_json_object(payload: object) -> dict[str, object]:
    if not isinstance(payload, dict):
        raise PrivacyValidationError("NAV payload must be a JSON object.")

    if not all(isinstance(key, str) for key in payload):
        raise PrivacyValidationError("NAV payload object keys must be strings.")

    return cast(dict[str, object], payload)


def _canonical_json(payload: dict[str, object]) -> str:
    try:
        return json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    except (TypeError, ValueError):
        raise PrivacyValidationError(
            "NAV payload must contain only JSON-serializable values."
        ) from None
