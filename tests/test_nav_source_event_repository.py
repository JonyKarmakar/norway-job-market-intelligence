from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any, Self, cast

import psycopg
import pytest
from psycopg.types.json import Jsonb

from norway_job_market_intelligence.database.exceptions import (
    SourceEventPersistenceError,
)
from norway_job_market_intelligence.database.repositories.nav_source_events import (
    NavSourceEventInput,
    insert_source_event,
)


class FakeCursor:
    def __init__(
        self,
        responses: list[tuple[int, ...] | None],
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

    def fetchone(self) -> tuple[int, ...] | None:
        return self.responses.pop(0)


class FakeConnection:
    def __init__(self, cursor: FakeCursor) -> None:
        self.fake_cursor = cursor

    def cursor(self) -> FakeCursor:
        return self.fake_cursor


def source_event_input() -> NavSourceEventInput:
    return NavSourceEventInput(
        source_event_id="synthetic-event-001",
        source_job_id="synthetic-job-001",
        feed_page_id="synthetic-page-001",
        source_status="ACTIVE",
        source_updated_at=datetime(2026, 1, 1, 8, 55, tzinfo=UTC),
        payload_hash="synthetic-hash-001",
        payload={
            "title": "Synthetic Data Engineer",
            "status": "ACTIVE",
        },
    )


def repository_connection(
    cursor: FakeCursor,
) -> psycopg.Connection[tuple[Any, ...]]:
    return cast(
        psycopg.Connection[tuple[Any, ...]],
        FakeConnection(cursor),
    )


def test_insert_source_event_returns_inserted_result() -> None:
    cursor = FakeCursor(responses=[(101,)])

    result = insert_source_event(
        repository_connection(cursor),
        source_event_input(),
    )

    assert result.event_id == 101
    assert result.inserted is True
    assert result.duplicate is False
    assert len(cursor.executions) == 1

    query, parameters = cursor.executions[0]

    assert "INSERT INTO nav_feed_events" in query
    assert "ON CONFLICT (source_event_id) DO NOTHING" in query
    assert "RETURNING event_id" in query
    assert parameters["source_event_id"] == "synthetic-event-001"
    assert parameters["source_job_id"] == "synthetic-job-001"
    assert parameters["payload_hash"] == "synthetic-hash-001"
    assert parameters["contact_data_removed"] is True
    assert isinstance(parameters["payload"], Jsonb)


def test_duplicate_source_event_returns_existing_event_id() -> None:
    cursor = FakeCursor(responses=[None, (101,)])

    result = insert_source_event(
        repository_connection(cursor),
        source_event_input(),
    )

    assert result.event_id == 101
    assert result.inserted is False
    assert result.duplicate is True
    assert len(cursor.executions) == 2
    assert "INSERT INTO nav_feed_events" in cursor.executions[0][0]
    assert "SELECT event_id" in cursor.executions[1][0]


def test_repository_does_not_target_current_state_or_progress() -> None:
    cursor = FakeCursor(responses=[None, (101,)])

    insert_source_event(
        repository_connection(cursor),
        source_event_input(),
    )

    executed_sql = "\n".join(query for query, _ in cursor.executions)

    assert "job_advertisements_current" not in executed_sql
    assert "nav_feed_progress" not in executed_sql
    assert "UPDATE " not in executed_sql.upper()


def test_database_error_is_translated_without_exposing_payload() -> None:
    sensitive_value = "fictional-private-contact"
    database_error = psycopg.errors.CheckViolation(f"Payload contained {sensitive_value}")
    cursor = FakeCursor(
        responses=[],
        error=database_error,
    )

    with pytest.raises(
        SourceEventPersistenceError,
        match="Unable to persist NAV source event",
    ) as captured_error:
        insert_source_event(
            repository_connection(cursor),
            source_event_input(),
        )

    assert sensitive_value not in str(captured_error.value)
    assert captured_error.value.__cause__ is database_error


def test_missing_duplicate_lookup_result_raises_safe_error() -> None:
    cursor = FakeCursor(responses=[None, None])

    with pytest.raises(
        SourceEventPersistenceError,
        match="Source-event insertion produced no database result",
    ):
        insert_source_event(
            repository_connection(cursor),
            source_event_input(),
        )
