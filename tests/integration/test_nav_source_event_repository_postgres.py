from collections.abc import Iterator
from dataclasses import replace
from datetime import UTC, datetime
from typing import Any, cast

import psycopg
import pytest

from norway_job_market_intelligence.database.connection import (
    open_database_connection,
)
from norway_job_market_intelligence.database.exceptions import (
    SourceEventPersistenceError,
)
from norway_job_market_intelligence.database.repositories.nav_source_events import (
    NavSourceEventInput,
    insert_source_event,
)
from norway_job_market_intelligence.ingestion.privacy import prepare_payload

pytestmark = pytest.mark.postgres


@pytest.fixture
def connection() -> Iterator[psycopg.Connection[tuple[Any, ...]]]:
    """Provide a clean caller-owned connection to the isolated test database."""

    database_connection = open_database_connection()

    with database_connection.transaction():
        database_connection.execute(
            """
            TRUNCATE TABLE
                nav_feed_progress,
                job_advertisements_current,
                nav_feed_events
            RESTART IDENTITY CASCADE
            """
        )

    try:
        yield database_connection
    finally:
        database_connection.close()


def make_source_event(
    *,
    source_event_id: str = "synthetic-event-001",
    source_job_id: str = "synthetic-job-001",
    feed_page_id: str | None = "synthetic-page-001",
    source_status: str | None = "ACTIVE",
    source_updated_at: datetime | None = datetime(
        2026,
        1,
        1,
        8,
        55,
        tzinfo=UTC,
    ),
    title: str = "Synthetic Data Engineer",
) -> NavSourceEventInput:
    """Build one fictional privacy-minimised source event."""

    prepared_payload = prepare_payload(
        {
            "uuid": source_job_id,
            "title": title,
            "status": source_status,
            "contactList": [
                {
                    "name": "Fictional Contact",
                }
            ],
        }
    )

    return NavSourceEventInput(
        source_event_id=source_event_id,
        source_job_id=source_job_id,
        feed_page_id=feed_page_id,
        source_status=source_status,
        source_updated_at=source_updated_at,
        payload_hash=prepared_payload.payload_hash,
        payload=prepared_payload.payload,
    )


def table_counts(
    connection: psycopg.Connection[tuple[Any, ...]],
) -> tuple[int, int, int]:
    """Return event, current-state and progress row counts."""

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                (SELECT COUNT(*) FROM nav_feed_events),
                (SELECT COUNT(*) FROM job_advertisements_current),
                (SELECT COUNT(*) FROM nav_feed_progress)
            """
        )
        row = cursor.fetchone()

    assert row is not None

    return int(row[0]), int(row[1]), int(row[2])


def test_insert_source_event_persists_expected_jsonb_row(
    connection: psycopg.Connection[tuple[Any, ...]],
) -> None:
    source_event = make_source_event()

    with connection.transaction():
        result = insert_source_event(connection, source_event)

    assert result.inserted is True
    assert result.duplicate is False
    assert result.event_id == 1

    with connection.transaction(), connection.cursor() as cursor:
        cursor.execute(
            """
                SELECT
                    event_id,
                    source_event_id,
                    source_job_id,
                    feed_page_id,
                    source_status,
                    source_updated_at,
                    payload_hash,
                    payload,
                    contact_data_removed,
                    JSONB_TYPEOF(payload),
                    ingested_at
                FROM nav_feed_events
                WHERE event_id = %s
                """,
            (result.event_id,),
        )
        row = cursor.fetchone()

    assert row is not None
    assert row[0] == result.event_id
    assert row[1] == source_event.source_event_id
    assert row[2] == source_event.source_job_id
    assert row[3] == source_event.feed_page_id
    assert row[4] == source_event.source_status
    assert row[5] == source_event.source_updated_at
    assert row[6] == source_event.payload_hash
    assert row[7] == source_event.payload
    assert row[8] is True
    assert row[9] == "object"
    assert row[10] is not None
    assert "contactList" not in row[7]

    assert table_counts(connection) == (1, 0, 0)


def test_duplicate_returns_existing_id_without_mutating_original_row(
    connection: psycopg.Connection[tuple[Any, ...]],
) -> None:
    original_event = make_source_event()

    with connection.transaction():
        first_result = insert_source_event(connection, original_event)

    duplicate_event = replace(
        original_event,
        source_job_id="synthetic-job-changed",
        feed_page_id="synthetic-page-changed",
        source_status="INACTIVE",
        payload_hash="synthetic-changed-hash",
        payload={
            "title": "Synthetic Changed Title",
            "status": "INACTIVE",
        },
    )

    with connection.transaction():
        duplicate_result = insert_source_event(
            connection,
            duplicate_event,
        )

    assert first_result.inserted is True
    assert duplicate_result.inserted is False
    assert duplicate_result.duplicate is True
    assert duplicate_result.event_id == first_result.event_id

    with connection.transaction(), connection.cursor() as cursor:
        cursor.execute(
            """
                SELECT
                    source_job_id,
                    feed_page_id,
                    source_status,
                    payload_hash,
                    payload
                FROM nav_feed_events
                WHERE source_event_id = %s
                """,
            (original_event.source_event_id,),
        )
        row = cursor.fetchone()

    assert row is not None
    assert row[0] == original_event.source_job_id
    assert row[1] == original_event.feed_page_id
    assert row[2] == original_event.source_status
    assert row[3] == original_event.payload_hash
    assert row[4] == original_event.payload

    assert table_counts(connection) == (1, 0, 0)


def test_second_event_preserves_history_for_same_advertisement(
    connection: psycopg.Connection[tuple[Any, ...]],
) -> None:
    first_event = make_source_event()

    second_event = make_source_event(
        source_event_id="synthetic-event-002",
        source_job_id=first_event.source_job_id,
        feed_page_id="synthetic-page-002",
        source_updated_at=datetime(
            2026,
            1,
            2,
            8,
            55,
            tzinfo=UTC,
        ),
        title="Synthetic Senior Data Engineer",
    )

    with connection.transaction():
        first_result = insert_source_event(connection, first_event)
        second_result = insert_source_event(connection, second_event)

    assert first_result.inserted is True
    assert second_result.inserted is True
    assert first_result.event_id != second_result.event_id

    with connection.transaction(), connection.cursor() as cursor:
        cursor.execute(
            """
                SELECT
                    source_event_id,
                    payload_hash
                FROM nav_feed_events
                WHERE source_job_id = %s
                ORDER BY event_id
                """,
            (first_event.source_job_id,),
        )
        rows = cursor.fetchall()

    assert rows == [
        (
            first_event.source_event_id,
            first_event.payload_hash,
        ),
        (
            second_event.source_event_id,
            second_event.payload_hash,
        ),
    ]

    assert table_counts(connection) == (2, 0, 0)


@pytest.mark.parametrize(
    "invalid_event",
    [
        replace(
            make_source_event(),
            payload={
                "title": "Synthetic Vacancy",
                "contactList": [],
            },
        ),
        replace(
            make_source_event(),
            source_event_id="   ",
        ),
        replace(
            make_source_event(),
            source_job_id="   ",
        ),
        replace(
            make_source_event(),
            payload_hash="   ",
        ),
        replace(
            make_source_event(),
            payload=cast(
                dict[str, object],
                ["not-a-json-object"],
            ),
        ),
        replace(
            make_source_event(),
            contact_data_removed=False,
        ),
    ],
    ids=[
        "contact-list",
        "blank-source-event-id",
        "blank-source-job-id",
        "blank-payload-hash",
        "non-object-payload",
        "contact-data-not-removed",
    ],
)
def test_database_constraints_remain_visible_to_repository(
    connection: psycopg.Connection[tuple[Any, ...]],
    invalid_event: NavSourceEventInput,
) -> None:
    with (
        pytest.raises(
            SourceEventPersistenceError,
            match="Unable to persist NAV source event",
        ) as captured_error,
        connection.transaction(),
    ):
        insert_source_event(connection, invalid_event)

    assert isinstance(
        captured_error.value.__cause__,
        psycopg.errors.CheckViolation,
    )
    assert table_counts(connection) == (0, 0, 0)


def test_failed_transaction_rolls_back_prior_event_and_connection_remains_usable(
    connection: psycopg.Connection[tuple[Any, ...]],
) -> None:
    valid_event = make_source_event()
    invalid_event = make_source_event(
        source_event_id="synthetic-event-invalid",
    )
    invalid_event = replace(
        invalid_event,
        payload={
            "title": "Synthetic Invalid Vacancy",
            "contactList": [],
        },
    )

    with pytest.raises(SourceEventPersistenceError), connection.transaction():
        insert_source_event(connection, valid_event)
        insert_source_event(connection, invalid_event)

    assert table_counts(connection) == (0, 0, 0)

    with connection.transaction():
        row = connection.execute("SELECT 1").fetchone()

    assert row == (1,)
