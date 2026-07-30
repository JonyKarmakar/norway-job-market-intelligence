import pytest

from norway_job_market_intelligence.ingestion.exceptions import (
    PrivacyValidationError,
)
from norway_job_market_intelligence.ingestion.privacy import (
    calculate_payload_hash,
    minimise_payload,
    prepare_payload,
    validate_minimised_payload,
)


def test_minimise_payload_removes_only_top_level_contact_list() -> None:
    source_payload: dict[str, object] = {
        "uuid": "advertisement-1",
        "contactList": [{"name": "Private Contact"}],
        "metadata": {
            "contactList": [{"type": "source-metadata"}],
        },
    }

    minimised_payload = minimise_payload(source_payload)

    assert "contactList" not in minimised_payload
    assert minimised_payload["metadata"] == {
        "contactList": [{"type": "source-metadata"}],
    }


def test_minimise_payload_does_not_mutate_source_payload() -> None:
    source_payload: dict[str, object] = {
        "uuid": "advertisement-1",
        "contactList": [{"name": "Private Contact"}],
        "metadata": {"source": "NAV"},
    }

    minimised_payload = minimise_payload(source_payload)

    assert source_payload == {
        "uuid": "advertisement-1",
        "contactList": [{"name": "Private Contact"}],
        "metadata": {"source": "NAV"},
    }
    assert minimised_payload is not source_payload
    assert minimised_payload["metadata"] is not source_payload["metadata"]


def test_minimise_payload_preserves_payload_without_contact_list() -> None:
    source_payload: dict[str, object] = {
        "uuid": "advertisement-2",
        "title": "Data Engineer",
    }

    minimised_payload = minimise_payload(source_payload)

    assert minimised_payload == source_payload
    assert minimised_payload is not source_payload


def test_minimise_payload_removes_null_contact_list() -> None:
    source_payload: dict[str, object] = {
        "uuid": "advertisement-3",
        "contactList": None,
    }

    assert minimise_payload(source_payload) == {
        "uuid": "advertisement-3",
    }


@pytest.mark.parametrize(
    "payload",
    [None, [], "not-an-object", 42],
)
def test_validation_rejects_non_object_payload(payload: object) -> None:
    with pytest.raises(
        PrivacyValidationError,
        match="NAV payload must be a JSON object",
    ):
        validate_minimised_payload(payload)


def test_validation_rejects_non_string_object_keys() -> None:
    with pytest.raises(
        PrivacyValidationError,
        match="NAV payload object keys must be strings",
    ):
        validate_minimised_payload({1: "invalid-key"})


def test_validation_rejects_unserializable_values() -> None:
    with pytest.raises(
        PrivacyValidationError,
        match="only JSON-serializable values",
    ):
        validate_minimised_payload({"skills": {"Python", "SQL"}})


def test_validation_rejects_non_finite_numbers() -> None:
    with pytest.raises(
        PrivacyValidationError,
        match="only JSON-serializable values",
    ):
        validate_minimised_payload({"confidence": float("nan")})


def test_payload_hash_is_stable_across_key_order() -> None:
    first_payload: dict[str, object] = {
        "title": "Data Engineer",
        "location": {
            "city": "Oslo",
            "country": "Norway",
        },
        "skills": ["Python", "SQL"],
    }
    second_payload: dict[str, object] = {
        "skills": ["Python", "SQL"],
        "location": {
            "country": "Norway",
            "city": "Oslo",
        },
        "title": "Data Engineer",
    }

    assert calculate_payload_hash(first_payload) == calculate_payload_hash(second_payload)


def test_payload_hash_matches_canonical_sha256_contract() -> None:
    payload: dict[str, object] = {
        "title": "Data Engineer",
        "location": {"city": "Oslo"},
        "active": True,
    }

    assert calculate_payload_hash(payload) == (
        "715bc915d2d113bac6812feff7cca0f4a440228134ce5eb5a31a28622446538f"
    )


def test_payload_hash_changes_when_payload_value_changes() -> None:
    original_payload: dict[str, object] = {
        "uuid": "advertisement-4",
        "title": "Data Engineer",
    }
    changed_payload: dict[str, object] = {
        "uuid": "advertisement-4",
        "title": "Senior Data Engineer",
    }

    assert calculate_payload_hash(original_payload) != calculate_payload_hash(changed_payload)


def test_payload_hash_rejects_unminimised_payload() -> None:
    payload: dict[str, object] = {
        "uuid": "advertisement-5",
        "contactList": [],
    }

    with pytest.raises(
        PrivacyValidationError,
        match="must not contain contactList",
    ):
        calculate_payload_hash(payload)


def test_prepare_payload_minimises_and_hashes_payload() -> None:
    source_payload: dict[str, object] = {
        "uuid": "advertisement-6",
        "title": "AI Engineer",
        "contactList": [{"name": "Private Contact"}],
    }

    prepared_payload = prepare_payload(source_payload)

    assert prepared_payload.payload == {
        "uuid": "advertisement-6",
        "title": "AI Engineer",
    }
    assert prepared_payload.payload_hash == calculate_payload_hash(prepared_payload.payload)
    assert len(prepared_payload.payload_hash) == 64
    assert "contactList" in source_payload
