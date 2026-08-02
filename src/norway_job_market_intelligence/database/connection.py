"""PostgreSQL connection boundary."""

from typing import Any

import psycopg

from norway_job_market_intelligence.config import DatabaseSettings
from norway_job_market_intelligence.database.exceptions import (
    DatabaseConnectionError,
)


def open_database_connection(
    settings: DatabaseSettings | None = None,
) -> psycopg.Connection[tuple[Any, ...]]:
    """Open a PostgreSQL connection for caller-owned use.

    The caller owns transaction handling and must close the returned
    connection when it is no longer needed.
    """

    resolved_settings = DatabaseSettings.from_environment() if settings is None else settings
    database_url = resolved_settings.require_database_url()

    try:
        return psycopg.connect(database_url)
    except (psycopg.OperationalError, psycopg.ProgrammingError) as error:
        raise DatabaseConnectionError("Unable to establish PostgreSQL connection.") from error
