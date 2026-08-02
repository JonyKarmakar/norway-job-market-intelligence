"""Persistence boundary for immutable NAV source events."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Final

import psycopg
from psycopg.types.json import Jsonb

from norway_job_market_intelligence.database.exceptions import (
    SourceEventPersistenceError,
)

_INSERT_SOURCE_EVENT_SQL: Final = """
    INSERT INTO nav_feed_events (
        source_event_id,
        source_job_id,
        feed_page_id,
        source_status,
        source_updated_at,
        payload_hash,
        payload,
        contact_data_removed
    )
    VALUES (
        %(source_event_id)s,
        %(source_job_id)s,
        %(feed_page_id)s,
        %(source_status)s,
        %(source_updated_at)s,
        %(payload_hash)s,
        %(payload)s,
        %(contact_data_removed)s
    )
    ON CONFLICT (source_event_id) DO NOTHING
    RETURNING event_id
"""

_SELECT_SOURCE_EVENT_ID_SQL: Final = """
    SELECT event_id
    FROM nav_feed_events
    WHERE source_event_id = %(source_event_id)s
"""


@dataclass(frozen=True, slots=True)
class NavSourceEventInput:
    """Typed source-event values required by the persistence boundary."""

    source_event_id: str
    source_job_id: str
    payload_hash: str
    payload: dict[str, object]
    feed_page_id: str | None = None
    source_status: str | None = None
    source_updated_at: datetime | None = None
    contact_data_removed: bool = True


@dataclass(frozen=True, slots=True)
class SourceEventInsertResult:
    """Outcome of inserting or rediscovering one immutable source event."""

    event_id: int
    inserted: bool

    @property
    def duplicate(self) -> bool:
        """Report whether the source event already existed."""

        return not self.inserted


def insert_source_event(
    connection: psycopg.Connection[tuple[Any, ...]],
    source_event: NavSourceEventInput,
) -> SourceEventInsertResult:
    """Insert one source event without committing the caller-owned transaction."""

    parameters: dict[str, object] = {
        "source_event_id": source_event.source_event_id,
        "source_job_id": source_event.source_job_id,
        "feed_page_id": source_event.feed_page_id,
        "source_status": source_event.source_status,
        "source_updated_at": source_event.source_updated_at,
        "payload_hash": source_event.payload_hash,
        "payload": Jsonb(source_event.payload),
        "contact_data_removed": source_event.contact_data_removed,
    }

    try:
        with connection.cursor() as cursor:
            cursor.execute(_INSERT_SOURCE_EVENT_SQL, parameters)
            inserted_row = cursor.fetchone()

            if inserted_row is not None:
                return SourceEventInsertResult(
                    event_id=int(inserted_row[0]),
                    inserted=True,
                )

            cursor.execute(
                _SELECT_SOURCE_EVENT_ID_SQL,
                {"source_event_id": source_event.source_event_id},
            )
            existing_row = cursor.fetchone()
    except psycopg.Error as error:
        raise SourceEventPersistenceError("Unable to persist NAV source event.") from error

    if existing_row is None:
        raise SourceEventPersistenceError("Source-event insertion produced no database result.")

    return SourceEventInsertResult(
        event_id=int(existing_row[0]),
        inserted=False,
    )
