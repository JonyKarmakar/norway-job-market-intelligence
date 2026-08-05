from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any, Self, cast

import psycopg
import pytest
from psycopg.types.json import Jsonb

from norway_job_market_intelligence.database.exceptions import (
    CurrentAdvertisementPersistenceError,
)
from norway_job_market_intelligence.database.repositories.current_advertisements import (
    CurrentAdvertisementInput,
    CurrentAdvertisementOperation,
    CurrentAdvertisementResult,
    maintain_current_advertisement,
)


class FakeCursor:
    def __init__(
        self,
        responses: list[tuple[object, ...] | None],
        error: psycopg.Error | None = None,
    ) -> None:
        self.responses = responses
        self.error = error
        self.executions: list[tuple[str, Mapping[str, object]]] = []

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exception_type: type[BaseException] | None,
        exception: BaseException | None,
        traceback: object,
    ) -> None:
        return None

    def execute(
        self,
        query: str,
        parameters: Mapping[str, object],
    ) -> None:
        self.executions.append((query, parameters))

        if self.error is not None:
            raise self.error

    def fetchone(self) -> tuple[object, ...] | None:
        return self.responses.pop(0)


class FakeConnection:
    def __init__(self, cursor: FakeCursor) -> None:
        self.fake_cursor = cursor

    def cursor(self) -> FakeCursor:
        return self.fake_cursor


def repository_connection(
    cursor: FakeCursor,
) -> psycopg.Connection[tuple[Any, ...]]:
    return cast(
        psycopg.Connection[tuple[Any, ...]],
        FakeConnection(cursor),
    )


def candidate_row(
    *,
    source_status: object = "ACTIVE",
    source_updated_at: datetime | None = datetime(
        2026,
        1,
        2,
        8,
        55,
        tzinfo=UTC,
    ),
) -> tuple[object, ...]:
    return (
        source_status,
        source_updated_at,
        datetime(2026, 1, 2, 9, 0, tzinfo=UTC),
        {
            "uuid": "synthetic-job-001",
            "title": "Synthetic Data Engineer",
            "status": source_status,
        },
    )


@pytest.mark.parametrize(
    ("operation", "expected_changed"),
    [
        (CurrentAdvertisementOperation.CREATED, True),
        (CurrentAdvertisementOperation.UPDATED, True),
        (CurrentAdvertisementOperation.UNCHANGED, False),
        (CurrentAdvertisementOperation.STALE_EVENT_IGNORED, False),
        (CurrentAdvertisementOperation.ORDERING_UNRESOLVED, False),
    ],
)
def test_result_reports_whether_current_state_changed(
    operation: CurrentAdvertisementOperation,
    expected_changed: bool,
) -> None:
    result = CurrentAdvertisementResult(
        source_job_id="synthetic-job-001",
        candidate_event_id=2,
        current_event_id=2,
        operation=operation,
        current_source_updated_at=datetime(
            2026,
            1,
            2,
            8,
            55,
            tzinfo=UTC,
        ),
    )

    assert result.changed is expected_changed


def test_first_event_creates_current_state_from_stored_event_values() -> None:
    cursor = FakeCursor(
        responses=[
            candidate_row(),
            (2,),
        ]
    )

    result = maintain_current_advertisement(
        repository_connection(cursor),
        CurrentAdvertisementInput(
            source_job_id="synthetic-job-001",
            candidate_event_id=2,
        ),
    )

    assert result.operation is CurrentAdvertisementOperation.CREATED
    assert result.changed is True
    assert result.current_event_id == 2
    assert result.current_source_updated_at == datetime(
        2026,
        1,
        2,
        8,
        55,
        tzinfo=UTC,
    )
    assert len(cursor.executions) == 2

    insert_query, parameters = cursor.executions[1]

    assert "INSERT INTO job_advertisements_current" in insert_query
    assert "ON CONFLICT (source_job_id) DO NOTHING" in insert_query
    assert parameters["source_job_id"] == "synthetic-job-001"
    assert parameters["candidate_event_id"] == 2
    assert parameters["source_status"] == "ACTIVE"
    assert isinstance(parameters["current_payload"], Jsonb)


def test_same_event_returns_unchanged_without_update() -> None:
    current_timestamp = datetime(2026, 1, 2, 8, 55, tzinfo=UTC)
    cursor = FakeCursor(
        responses=[
            candidate_row(source_updated_at=current_timestamp),
            None,
            (2, current_timestamp),
        ]
    )

    result = maintain_current_advertisement(
        repository_connection(cursor),
        CurrentAdvertisementInput(
            source_job_id="synthetic-job-001",
            candidate_event_id=2,
        ),
    )

    assert result.operation is CurrentAdvertisementOperation.UNCHANGED
    assert result.changed is False
    assert result.current_event_id == 2
    assert len(cursor.executions) == 3
    assert not any("UPDATE job_advertisements_current" in query for query, _ in cursor.executions)


def test_older_event_is_ignored_without_update() -> None:
    candidate_timestamp = datetime(2026, 1, 1, 8, 55, tzinfo=UTC)
    current_timestamp = datetime(2026, 1, 2, 8, 55, tzinfo=UTC)
    cursor = FakeCursor(
        responses=[
            candidate_row(source_updated_at=candidate_timestamp),
            None,
            (2, current_timestamp),
        ]
    )

    result = maintain_current_advertisement(
        repository_connection(cursor),
        CurrentAdvertisementInput(
            source_job_id="synthetic-job-001",
            candidate_event_id=1,
        ),
    )

    assert result.operation is CurrentAdvertisementOperation.STALE_EVENT_IGNORED
    assert result.current_event_id == 2
    assert result.current_source_updated_at == current_timestamp
    assert not any("UPDATE job_advertisements_current" in query for query, _ in cursor.executions)


@pytest.mark.parametrize(
    ("candidate_timestamp", "current_timestamp"),
    [
        (
            datetime(2026, 1, 2, 8, 55, tzinfo=UTC),
            datetime(2026, 1, 2, 8, 55, tzinfo=UTC),
        ),
        (
            None,
            datetime(2026, 1, 2, 8, 55, tzinfo=UTC),
        ),
        (
            datetime(2026, 1, 2, 8, 55, tzinfo=UTC),
            None,
        ),
    ],
)
def test_unorderable_events_leave_current_state_unchanged(
    candidate_timestamp: datetime | None,
    current_timestamp: datetime | None,
) -> None:
    cursor = FakeCursor(
        responses=[
            candidate_row(source_updated_at=candidate_timestamp),
            None,
            (1, current_timestamp),
        ]
    )

    result = maintain_current_advertisement(
        repository_connection(cursor),
        CurrentAdvertisementInput(
            source_job_id="synthetic-job-001",
            candidate_event_id=2,
        ),
    )

    assert result.operation is CurrentAdvertisementOperation.ORDERING_UNRESOLVED
    assert result.current_event_id == 1
    assert result.current_source_updated_at == current_timestamp
    assert not any("UPDATE job_advertisements_current" in query for query, _ in cursor.executions)


def test_newer_event_updates_current_state() -> None:
    candidate_timestamp = datetime(2026, 1, 3, 8, 55, tzinfo=UTC)
    current_timestamp = datetime(2026, 1, 2, 8, 55, tzinfo=UTC)
    cursor = FakeCursor(
        responses=[
            candidate_row(source_updated_at=candidate_timestamp),
            None,
            (1, current_timestamp),
            (2,),
        ]
    )

    result = maintain_current_advertisement(
        repository_connection(cursor),
        CurrentAdvertisementInput(
            source_job_id="synthetic-job-001",
            candidate_event_id=2,
        ),
    )

    assert result.operation is CurrentAdvertisementOperation.UPDATED
    assert result.changed is True
    assert result.current_event_id == 2
    assert result.current_source_updated_at == candidate_timestamp
    assert "UPDATE job_advertisements_current" in cursor.executions[3][0]


def test_missing_or_mismatched_event_raises_safe_error() -> None:
    cursor = FakeCursor(responses=[None])

    with pytest.raises(
        CurrentAdvertisementPersistenceError,
        match="Stored NAV source event was not found",
    ):
        maintain_current_advertisement(
            repository_connection(cursor),
            CurrentAdvertisementInput(
                source_job_id="synthetic-job-001",
                candidate_event_id=99,
            ),
        )


@pytest.mark.parametrize("invalid_status", [None, "", "   "])
def test_event_without_usable_status_raises_safe_error(
    invalid_status: object,
) -> None:
    cursor = FakeCursor(
        responses=[
            candidate_row(source_status=invalid_status),
        ]
    )

    with pytest.raises(
        CurrentAdvertisementPersistenceError,
        match="does not contain a usable status",
    ):
        maintain_current_advertisement(
            repository_connection(cursor),
            CurrentAdvertisementInput(
                source_job_id="synthetic-job-001",
                candidate_event_id=1,
            ),
        )


def test_database_error_is_translated_without_exposing_payload() -> None:
    sensitive_value = "fictional-private-contact"
    database_error = psycopg.errors.CheckViolation(f"Payload contained {sensitive_value}")
    cursor = FakeCursor(
        responses=[],
        error=database_error,
    )

    with pytest.raises(
        CurrentAdvertisementPersistenceError,
        match="Unable to maintain current NAV advertisement state",
    ) as captured_error:
        maintain_current_advertisement(
            repository_connection(cursor),
            CurrentAdvertisementInput(
                source_job_id="synthetic-job-001",
                candidate_event_id=1,
            ),
        )

    assert sensitive_value not in str(captured_error.value)
    assert captured_error.value.__cause__ is database_error


def test_repository_does_not_target_feed_progress() -> None:
    cursor = FakeCursor(
        responses=[
            candidate_row(),
            (1,),
        ]
    )

    maintain_current_advertisement(
        repository_connection(cursor),
        CurrentAdvertisementInput(
            source_job_id="synthetic-job-001",
            candidate_event_id=1,
        ),
    )

    executed_sql = "\n".join(query for query, _ in cursor.executions)

    assert "nav_feed_progress" not in executed_sql
