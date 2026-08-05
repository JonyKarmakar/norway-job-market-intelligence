from collections.abc import Iterator
from datetime import UTC, datetime
from typing import Any

import psycopg
import pytest

from norway_job_market_intelligence.database.connection import (
    open_database_connection,
)
from norway_job_market_intelligence.database.exceptions import (
    CurrentAdvertisementPersistenceError,
)
from norway_job_market_intelligence.database.repositories.current_advertisements import (
    CurrentAdvertisementInput,
    CurrentAdvertisementOperation,
    maintain_current_advertisement,
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
    source_event_id: str,
    source_job_id: str = "synthetic-job-001",
    source_status: str | None = "ACTIVE",
    source_updated_at: datetime | None,
    title: str,
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
        feed_page_id="synthetic-page-001",
        source_status=source_status,
        source_updated_at=source_updated_at,
        payload_hash=prepared_payload.payload_hash,
        payload=prepared_payload.payload,
    )


def read_current_row(
    connection: psycopg.Connection[tuple[Any, ...]],
    source_job_id: str,
) -> tuple[Any, ...] | None:
    """Read the complete current-state row and referenced ingestion time."""

    with connection.transaction(), connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                current_ad.source_job_id,
                current_ad.latest_event_id,
                current_ad.source_status,
                current_ad.source_updated_at,
                current_ad.first_seen_at,
                current_ad.last_seen_at,
                current_ad.current_payload,
                event.ingested_at
            FROM job_advertisements_current AS current_ad
            JOIN nav_feed_events AS event
              ON event.event_id = current_ad.latest_event_id
             AND event.source_job_id = current_ad.source_job_id
            WHERE current_ad.source_job_id = %s
            """,
            (source_job_id,),
        )
        return cursor.fetchone()


def table_counts(
    connection: psycopg.Connection[tuple[Any, ...]],
) -> tuple[int, int, int]:
    """Return source-event, current-state and feed-progress row counts."""

    with connection.transaction(), connection.cursor() as cursor:
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


def test_first_event_creates_current_state_from_stored_event(
    connection: psycopg.Connection[tuple[Any, ...]],
) -> None:
    source_event = make_source_event(
        source_event_id="synthetic-event-001",
        source_updated_at=datetime(2026, 1, 1, 8, 55, tzinfo=UTC),
        title="Synthetic Data Engineer",
    )

    with connection.transaction():
        event_result = insert_source_event(connection, source_event)
        result = maintain_current_advertisement(
            connection,
            CurrentAdvertisementInput(
                source_job_id=source_event.source_job_id,
                candidate_event_id=event_result.event_id,
            ),
        )

    assert result.operation is CurrentAdvertisementOperation.CREATED
    assert result.changed is True
    assert result.current_event_id == event_result.event_id

    row = read_current_row(connection, source_event.source_job_id)

    assert row is not None
    assert row[0] == source_event.source_job_id
    assert row[1] == event_result.event_id
    assert row[2] == source_event.source_status
    assert row[3] == source_event.source_updated_at
    assert row[4] == row[7]
    assert row[5] == row[7]
    assert row[6] == source_event.payload
    assert "contactList" not in row[6]
    assert table_counts(connection) == (1, 1, 0)


def test_newer_event_updates_state_and_preserves_first_seen(
    connection: psycopg.Connection[tuple[Any, ...]],
) -> None:
    first_event = make_source_event(
        source_event_id="synthetic-event-001",
        source_updated_at=datetime(2026, 1, 1, 8, 55, tzinfo=UTC),
        title="Synthetic Data Engineer",
    )
    second_event = make_source_event(
        source_event_id="synthetic-event-002",
        source_updated_at=datetime(2026, 1, 2, 8, 55, tzinfo=UTC),
        title="Synthetic Senior Data Engineer",
    )

    with connection.transaction():
        first_event_result = insert_source_event(connection, first_event)
        first_result = maintain_current_advertisement(
            connection,
            CurrentAdvertisementInput(
                source_job_id=first_event.source_job_id,
                candidate_event_id=first_event_result.event_id,
            ),
        )

    initial_row = read_current_row(connection, first_event.source_job_id)
    assert initial_row is not None
    assert first_result.operation is CurrentAdvertisementOperation.CREATED

    with connection.transaction():
        second_event_result = insert_source_event(connection, second_event)
        second_result = maintain_current_advertisement(
            connection,
            CurrentAdvertisementInput(
                source_job_id=second_event.source_job_id,
                candidate_event_id=second_event_result.event_id,
            ),
        )

    updated_row = read_current_row(connection, second_event.source_job_id)

    assert updated_row is not None
    assert second_result.operation is CurrentAdvertisementOperation.UPDATED
    assert second_result.current_event_id == second_event_result.event_id
    assert updated_row[1] == second_event_result.event_id
    assert updated_row[2] == "ACTIVE"
    assert updated_row[3] == second_event.source_updated_at
    assert updated_row[4] == initial_row[4]
    assert updated_row[5] >= initial_row[5]
    assert updated_row[5] == updated_row[7]
    assert updated_row[6] == second_event.payload
    assert table_counts(connection) == (2, 1, 0)


def test_older_event_remains_in_history_without_replacing_current_state(
    connection: psycopg.Connection[tuple[Any, ...]],
) -> None:
    current_event = make_source_event(
        source_event_id="synthetic-event-newer",
        source_updated_at=datetime(2026, 1, 3, 8, 55, tzinfo=UTC),
        title="Synthetic Current Data Engineer",
    )
    older_event = make_source_event(
        source_event_id="synthetic-event-older",
        source_updated_at=datetime(2026, 1, 2, 8, 55, tzinfo=UTC),
        title="Synthetic Older Data Engineer",
    )

    with connection.transaction():
        current_event_result = insert_source_event(connection, current_event)
        maintain_current_advertisement(
            connection,
            CurrentAdvertisementInput(
                source_job_id=current_event.source_job_id,
                candidate_event_id=current_event_result.event_id,
            ),
        )

    row_before = read_current_row(connection, current_event.source_job_id)

    with connection.transaction():
        older_event_result = insert_source_event(connection, older_event)
        result = maintain_current_advertisement(
            connection,
            CurrentAdvertisementInput(
                source_job_id=older_event.source_job_id,
                candidate_event_id=older_event_result.event_id,
            ),
        )

    row_after = read_current_row(connection, current_event.source_job_id)

    assert result.operation is CurrentAdvertisementOperation.STALE_EVENT_IGNORED
    assert result.changed is False
    assert result.current_event_id == current_event_result.event_id
    assert row_after == row_before
    assert table_counts(connection) == (2, 1, 0)


def test_equal_source_timestamps_leave_ordering_unresolved(
    connection: psycopg.Connection[tuple[Any, ...]],
) -> None:
    shared_timestamp = datetime(2026, 1, 2, 8, 55, tzinfo=UTC)
    first_event = make_source_event(
        source_event_id="synthetic-event-001",
        source_updated_at=shared_timestamp,
        title="Synthetic First Data Engineer",
    )
    second_event = make_source_event(
        source_event_id="synthetic-event-002",
        source_updated_at=shared_timestamp,
        title="Synthetic Second Data Engineer",
    )

    with connection.transaction():
        first_event_result = insert_source_event(connection, first_event)
        maintain_current_advertisement(
            connection,
            CurrentAdvertisementInput(
                source_job_id=first_event.source_job_id,
                candidate_event_id=first_event_result.event_id,
            ),
        )

    row_before = read_current_row(connection, first_event.source_job_id)

    with connection.transaction():
        second_event_result = insert_source_event(connection, second_event)
        result = maintain_current_advertisement(
            connection,
            CurrentAdvertisementInput(
                source_job_id=second_event.source_job_id,
                candidate_event_id=second_event_result.event_id,
            ),
        )

    row_after = read_current_row(connection, first_event.source_job_id)

    assert result.operation is CurrentAdvertisementOperation.ORDERING_UNRESOLVED
    assert result.changed is False
    assert result.current_event_id == first_event_result.event_id
    assert row_after == row_before
    assert table_counts(connection) == (2, 1, 0)


@pytest.mark.parametrize(
    ("current_timestamp", "candidate_timestamp"),
    [
        (
            None,
            datetime(2026, 1, 2, 8, 55, tzinfo=UTC),
        ),
        (
            datetime(2026, 1, 1, 8, 55, tzinfo=UTC),
            None,
        ),
    ],
)
def test_missing_source_timestamp_leaves_ordering_unresolved(
    connection: psycopg.Connection[tuple[Any, ...]],
    current_timestamp: datetime | None,
    candidate_timestamp: datetime | None,
) -> None:
    first_event = make_source_event(
        source_event_id="synthetic-event-001",
        source_updated_at=current_timestamp,
        title="Synthetic Current Data Engineer",
    )
    second_event = make_source_event(
        source_event_id="synthetic-event-002",
        source_updated_at=candidate_timestamp,
        title="Synthetic Candidate Data Engineer",
    )

    with connection.transaction():
        first_event_result = insert_source_event(connection, first_event)
        maintain_current_advertisement(
            connection,
            CurrentAdvertisementInput(
                source_job_id=first_event.source_job_id,
                candidate_event_id=first_event_result.event_id,
            ),
        )

    row_before = read_current_row(connection, first_event.source_job_id)

    with connection.transaction():
        second_event_result = insert_source_event(connection, second_event)
        result = maintain_current_advertisement(
            connection,
            CurrentAdvertisementInput(
                source_job_id=second_event.source_job_id,
                candidate_event_id=second_event_result.event_id,
            ),
        )

    row_after = read_current_row(connection, first_event.source_job_id)

    assert result.operation is CurrentAdvertisementOperation.ORDERING_UNRESOLVED
    assert result.changed is False
    assert result.current_event_id == first_event_result.event_id
    assert row_after == row_before
    assert table_counts(connection) == (2, 1, 0)


def test_newer_inactive_event_becomes_current_without_deletion(
    connection: psycopg.Connection[tuple[Any, ...]],
) -> None:
    active_event = make_source_event(
        source_event_id="synthetic-event-active",
        source_updated_at=datetime(2026, 1, 1, 8, 55, tzinfo=UTC),
        title="Synthetic Active Data Engineer",
    )
    inactive_event = make_source_event(
        source_event_id="synthetic-event-inactive",
        source_status="INACTIVE",
        source_updated_at=datetime(2026, 1, 2, 8, 55, tzinfo=UTC),
        title="Synthetic Inactive Data Engineer",
    )

    with connection.transaction():
        active_result = insert_source_event(connection, active_event)
        maintain_current_advertisement(
            connection,
            CurrentAdvertisementInput(
                source_job_id=active_event.source_job_id,
                candidate_event_id=active_result.event_id,
            ),
        )

    initial_row = read_current_row(connection, active_event.source_job_id)
    assert initial_row is not None

    with connection.transaction():
        inactive_result = insert_source_event(connection, inactive_event)
        result = maintain_current_advertisement(
            connection,
            CurrentAdvertisementInput(
                source_job_id=inactive_event.source_job_id,
                candidate_event_id=inactive_result.event_id,
            ),
        )

    final_row = read_current_row(connection, inactive_event.source_job_id)

    assert final_row is not None
    assert result.operation is CurrentAdvertisementOperation.UPDATED
    assert final_row[1] == inactive_result.event_id
    assert final_row[2] == "INACTIVE"
    assert final_row[4] == initial_row[4]
    assert final_row[5] >= initial_row[5]
    assert final_row[6] == inactive_event.payload
    assert table_counts(connection) == (2, 1, 0)


def test_reprocessing_current_event_returns_unchanged(
    connection: psycopg.Connection[tuple[Any, ...]],
) -> None:
    source_event = make_source_event(
        source_event_id="synthetic-event-unchanged",
        source_updated_at=datetime(2026, 1, 1, 8, 55, tzinfo=UTC),
        title="Synthetic Unchanged Data Engineer",
    )

    with connection.transaction():
        event_result = insert_source_event(connection, source_event)
        created_result = maintain_current_advertisement(
            connection,
            CurrentAdvertisementInput(
                source_job_id=source_event.source_job_id,
                candidate_event_id=event_result.event_id,
            ),
        )

    row_before = read_current_row(connection, source_event.source_job_id)

    with connection.transaction():
        unchanged_result = maintain_current_advertisement(
            connection,
            CurrentAdvertisementInput(
                source_job_id=source_event.source_job_id,
                candidate_event_id=event_result.event_id,
            ),
        )

    row_after = read_current_row(connection, source_event.source_job_id)

    assert created_result.operation is CurrentAdvertisementOperation.CREATED
    assert unchanged_result.operation is CurrentAdvertisementOperation.UNCHANGED
    assert unchanged_result.changed is False
    assert unchanged_result.current_event_id == event_result.event_id
    assert row_after == row_before
    assert table_counts(connection) == (1, 1, 0)


def test_event_owned_by_another_advertisement_is_rejected_safely(
    connection: psycopg.Connection[tuple[Any, ...]],
) -> None:
    source_event = make_source_event(
        source_event_id="synthetic-event-owned-by-b",
        source_job_id="synthetic-job-b",
        source_updated_at=datetime(2026, 1, 1, 8, 55, tzinfo=UTC),
        title="Synthetic Platform Engineer",
    )

    with connection.transaction():
        event_result = insert_source_event(connection, source_event)

    with (
        pytest.raises(
            CurrentAdvertisementPersistenceError,
            match="Stored NAV source event was not found",
        ),
        connection.transaction(),
    ):
        maintain_current_advertisement(
            connection,
            CurrentAdvertisementInput(
                source_job_id="synthetic-job-a",
                candidate_event_id=event_result.event_id,
            ),
        )

    assert read_current_row(connection, "synthetic-job-a") is None
    assert read_current_row(connection, "synthetic-job-b") is None
    assert table_counts(connection) == (1, 0, 0)


def test_missing_source_event_leaves_current_state_unchanged(
    connection: psycopg.Connection[tuple[Any, ...]],
) -> None:
    with (
        pytest.raises(
            CurrentAdvertisementPersistenceError,
            match="Stored NAV source event was not found",
        ),
        connection.transaction(),
    ):
        maintain_current_advertisement(
            connection,
            CurrentAdvertisementInput(
                source_job_id="synthetic-job-missing",
                candidate_event_id=999,
            ),
        )

    assert table_counts(connection) == (0, 0, 0)


def test_event_without_usable_status_cannot_create_current_state(
    connection: psycopg.Connection[tuple[Any, ...]],
) -> None:
    source_event = make_source_event(
        source_event_id="synthetic-event-no-status",
        source_status=None,
        source_updated_at=datetime(2026, 1, 1, 8, 55, tzinfo=UTC),
        title="Synthetic Statusless Data Engineer",
    )

    with connection.transaction():
        event_result = insert_source_event(connection, source_event)

    with (
        pytest.raises(
            CurrentAdvertisementPersistenceError,
            match="does not contain a usable status",
        ),
        connection.transaction(),
    ):
        maintain_current_advertisement(
            connection,
            CurrentAdvertisementInput(
                source_job_id=source_event.source_job_id,
                candidate_event_id=event_result.event_id,
            ),
        )

    assert read_current_row(connection, source_event.source_job_id) is None
    assert table_counts(connection) == (1, 0, 0)


def test_caller_can_roll_back_event_and_current_state_together(
    connection: psycopg.Connection[tuple[Any, ...]],
) -> None:
    source_event = make_source_event(
        source_event_id="synthetic-event-rollback",
        source_updated_at=datetime(2026, 1, 1, 8, 55, tzinfo=UTC),
        title="Synthetic Rollback Data Engineer",
    )

    with (
        pytest.raises(RuntimeError, match="synthetic transaction failure"),
        connection.transaction(),
    ):
        event_result = insert_source_event(connection, source_event)
        result = maintain_current_advertisement(
            connection,
            CurrentAdvertisementInput(
                source_job_id=source_event.source_job_id,
                candidate_event_id=event_result.event_id,
            ),
        )

        assert result.operation is CurrentAdvertisementOperation.CREATED
        raise RuntimeError("synthetic transaction failure")

    assert table_counts(connection) == (0, 0, 0)

    with connection.transaction():
        row = connection.execute("SELECT 1").fetchone()

    assert row == (1,)
