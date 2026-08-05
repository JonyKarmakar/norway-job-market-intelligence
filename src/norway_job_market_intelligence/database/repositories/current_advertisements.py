"""Persistence boundary for current NAV advertisement state."""

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any, Final, cast

import psycopg
from psycopg.types.json import Jsonb

from norway_job_market_intelligence.database.exceptions import (
    CurrentAdvertisementPersistenceError,
)

_SELECT_CANDIDATE_EVENT_SQL: Final = """
    SELECT
        source_status,
        source_updated_at,
        ingested_at,
        payload
    FROM nav_feed_events
    WHERE event_id = %(candidate_event_id)s
      AND source_job_id = %(source_job_id)s
"""

_INSERT_CURRENT_ADVERTISEMENT_SQL: Final = """
    INSERT INTO job_advertisements_current (
        source_job_id,
        latest_event_id,
        source_status,
        source_updated_at,
        first_seen_at,
        last_seen_at,
        current_payload
    )
    VALUES (
        %(source_job_id)s,
        %(candidate_event_id)s,
        %(source_status)s,
        %(source_updated_at)s,
        %(candidate_ingested_at)s,
        %(candidate_ingested_at)s,
        %(current_payload)s
    )
    ON CONFLICT (source_job_id) DO NOTHING
    RETURNING latest_event_id
"""

_SELECT_CURRENT_FOR_UPDATE_SQL: Final = """
    SELECT
        current_ad.latest_event_id,
        current_event.source_updated_at
    FROM job_advertisements_current AS current_ad
    JOIN nav_feed_events AS current_event
      ON current_event.event_id = current_ad.latest_event_id
     AND current_event.source_job_id = current_ad.source_job_id
    WHERE current_ad.source_job_id = %(source_job_id)s
    FOR UPDATE OF current_ad
"""

_UPDATE_CURRENT_ADVERTISEMENT_SQL: Final = """
    UPDATE job_advertisements_current
    SET
        latest_event_id = %(candidate_event_id)s,
        source_status = %(source_status)s,
        source_updated_at = %(source_updated_at)s,
        last_seen_at = GREATEST(
            last_seen_at,
            %(candidate_ingested_at)s
        ),
        current_payload = %(current_payload)s
    WHERE source_job_id = %(source_job_id)s
    RETURNING latest_event_id
"""


class CurrentAdvertisementOperation(StrEnum):
    """Meaningful outcomes from current-state maintenance."""

    CREATED = "created"
    UPDATED = "updated"
    UNCHANGED = "unchanged"
    STALE_EVENT_IGNORED = "stale_event_ignored"
    ORDERING_UNRESOLVED = "ordering_unresolved"


@dataclass(frozen=True, slots=True)
class CurrentAdvertisementInput:
    """Identifiers required to evaluate one stored source event."""

    source_job_id: str
    candidate_event_id: int


@dataclass(frozen=True, slots=True)
class CurrentAdvertisementResult:
    """Outcome of evaluating one event against current advertisement state."""

    source_job_id: str
    candidate_event_id: int
    current_event_id: int
    operation: CurrentAdvertisementOperation
    current_source_updated_at: datetime | None

    @property
    def changed(self) -> bool:
        """Report whether the current-state row was inserted or updated."""

        return self.operation in {
            CurrentAdvertisementOperation.CREATED,
            CurrentAdvertisementOperation.UPDATED,
        }


def maintain_current_advertisement(
    connection: psycopg.Connection[tuple[Any, ...]],
    advertisement: CurrentAdvertisementInput,
) -> CurrentAdvertisementResult:
    """Maintain current state without committing the caller-owned transaction."""

    lookup_parameters: dict[str, object] = {
        "source_job_id": advertisement.source_job_id,
        "candidate_event_id": advertisement.candidate_event_id,
    }

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                _SELECT_CANDIDATE_EVENT_SQL,
                lookup_parameters,
            )
            candidate_row = cursor.fetchone()

            if candidate_row is None:
                raise CurrentAdvertisementPersistenceError(
                    "Stored NAV source event was not found for the advertisement."
                )

            source_status_value = candidate_row[0]

            if not isinstance(source_status_value, str) or not source_status_value.strip():
                raise CurrentAdvertisementPersistenceError(
                    "Stored NAV source event does not contain a usable status."
                )

            candidate_source_updated_at = cast(
                datetime | None,
                candidate_row[1],
            )
            candidate_ingested_at = cast(datetime, candidate_row[2])
            candidate_payload = cast(dict[str, object], candidate_row[3])

            persistence_parameters: dict[str, object] = {
                **lookup_parameters,
                "source_status": source_status_value,
                "source_updated_at": candidate_source_updated_at,
                "candidate_ingested_at": candidate_ingested_at,
                "current_payload": Jsonb(candidate_payload),
            }

            cursor.execute(
                _INSERT_CURRENT_ADVERTISEMENT_SQL,
                persistence_parameters,
            )
            created_row = cursor.fetchone()

            if created_row is not None:
                return CurrentAdvertisementResult(
                    source_job_id=advertisement.source_job_id,
                    candidate_event_id=advertisement.candidate_event_id,
                    current_event_id=int(created_row[0]),
                    operation=CurrentAdvertisementOperation.CREATED,
                    current_source_updated_at=candidate_source_updated_at,
                )

            cursor.execute(
                _SELECT_CURRENT_FOR_UPDATE_SQL,
                lookup_parameters,
            )
            current_row = cursor.fetchone()

            if current_row is None:
                raise CurrentAdvertisementPersistenceError(
                    "Current advertisement state produced no database result."
                )

            current_event_id = int(current_row[0])
            current_source_updated_at = cast(
                datetime | None,
                current_row[1],
            )

            if current_event_id == advertisement.candidate_event_id:
                return CurrentAdvertisementResult(
                    source_job_id=advertisement.source_job_id,
                    candidate_event_id=advertisement.candidate_event_id,
                    current_event_id=current_event_id,
                    operation=CurrentAdvertisementOperation.UNCHANGED,
                    current_source_updated_at=current_source_updated_at,
                )

            if candidate_source_updated_at is None or current_source_updated_at is None:
                return CurrentAdvertisementResult(
                    source_job_id=advertisement.source_job_id,
                    candidate_event_id=advertisement.candidate_event_id,
                    current_event_id=current_event_id,
                    operation=CurrentAdvertisementOperation.ORDERING_UNRESOLVED,
                    current_source_updated_at=current_source_updated_at,
                )

            if candidate_source_updated_at < current_source_updated_at:
                return CurrentAdvertisementResult(
                    source_job_id=advertisement.source_job_id,
                    candidate_event_id=advertisement.candidate_event_id,
                    current_event_id=current_event_id,
                    operation=CurrentAdvertisementOperation.STALE_EVENT_IGNORED,
                    current_source_updated_at=current_source_updated_at,
                )

            if candidate_source_updated_at == current_source_updated_at:
                return CurrentAdvertisementResult(
                    source_job_id=advertisement.source_job_id,
                    candidate_event_id=advertisement.candidate_event_id,
                    current_event_id=current_event_id,
                    operation=CurrentAdvertisementOperation.ORDERING_UNRESOLVED,
                    current_source_updated_at=current_source_updated_at,
                )

            cursor.execute(
                _UPDATE_CURRENT_ADVERTISEMENT_SQL,
                persistence_parameters,
            )
            updated_row = cursor.fetchone()

            if updated_row is None:
                raise CurrentAdvertisementPersistenceError(
                    "Current advertisement update produced no database result."
                )

            return CurrentAdvertisementResult(
                source_job_id=advertisement.source_job_id,
                candidate_event_id=advertisement.candidate_event_id,
                current_event_id=int(updated_row[0]),
                operation=CurrentAdvertisementOperation.UPDATED,
                current_source_updated_at=candidate_source_updated_at,
            )
    except psycopg.Error as error:
        raise CurrentAdvertisementPersistenceError(
            "Unable to maintain current NAV advertisement state."
        ) from error
