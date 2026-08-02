from typing import Any, cast

import psycopg
import pytest

from norway_job_market_intelligence.config import DatabaseSettings
from norway_job_market_intelligence.database.connection import (
    open_database_connection,
)
from norway_job_market_intelligence.database.exceptions import (
    DatabaseConfigurationError,
    DatabaseConnectionError,
)


def test_open_database_connection_uses_injected_settings(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database_url = (
        "postgresql://fictional-user:fictional-password@localhost:5432/fictional-database"
    )
    settings = DatabaseSettings(database_url=database_url)

    captured_urls: list[str] = []
    fake_connection = cast(
        psycopg.Connection[tuple[Any, ...]],
        object(),
    )

    def fake_connect(
        conninfo: str,
    ) -> psycopg.Connection[tuple[Any, ...]]:
        captured_urls.append(conninfo)
        return fake_connection

    monkeypatch.setattr(psycopg, "connect", fake_connect)

    connection = open_database_connection(settings)

    assert connection is fake_connection
    assert captured_urls == [database_url]


def test_open_database_connection_loads_environment_by_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database_url = (
        "postgresql://fictional-user:fictional-password@localhost:5432/fictional-database"
    )
    monkeypatch.setenv("DATABASE_URL", database_url)

    captured_urls: list[str] = []
    fake_connection = cast(
        psycopg.Connection[tuple[Any, ...]],
        object(),
    )

    def fake_connect(
        conninfo: str,
    ) -> psycopg.Connection[tuple[Any, ...]]:
        captured_urls.append(conninfo)
        return fake_connection

    monkeypatch.setattr(psycopg, "connect", fake_connect)

    connection = open_database_connection()

    assert connection is fake_connection
    assert captured_urls == [database_url]


def test_missing_database_configuration_prevents_connection_attempt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    connection_attempted = False

    def fake_connect(
        conninfo: str,
    ) -> psycopg.Connection[tuple[Any, ...]]:
        nonlocal connection_attempted
        connection_attempted = True
        raise AssertionError(f"Unexpected connection attempt: {conninfo}")

    monkeypatch.setattr(psycopg, "connect", fake_connect)

    with pytest.raises(
        DatabaseConfigurationError,
        match="DATABASE_URL is required before database persistence",
    ):
        open_database_connection(DatabaseSettings())

    assert connection_attempted is False


def test_operational_error_is_translated_without_exposing_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database_url = (
        "postgresql://fictional-user:fictional-password@localhost:5432/fictional-database"
    )

    def fake_connect(
        conninfo: str,
    ) -> psycopg.Connection[tuple[Any, ...]]:
        raise psycopg.OperationalError(f"Unable to connect using {conninfo}")

    monkeypatch.setattr(psycopg, "connect", fake_connect)

    with pytest.raises(
        DatabaseConnectionError,
        match="Unable to establish PostgreSQL connection",
    ) as captured_error:
        open_database_connection(DatabaseSettings(database_url=database_url))

    error_message = str(captured_error.value)

    assert database_url not in error_message
    assert "fictional-password" not in error_message
    assert isinstance(
        captured_error.value.__cause__,
        psycopg.OperationalError,
    )


def test_invalid_connection_information_is_translated_safely(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database_url = (
        "postgresql://fictional-user:fictional-password@localhost:5432/fictional-database"
    )

    def fake_connect(
        conninfo: str,
    ) -> psycopg.Connection[tuple[Any, ...]]:
        raise psycopg.ProgrammingError(f"Invalid connection information: {conninfo}")

    monkeypatch.setattr(psycopg, "connect", fake_connect)

    with pytest.raises(
        DatabaseConnectionError,
        match="Unable to establish PostgreSQL connection",
    ) as captured_error:
        open_database_connection(DatabaseSettings(database_url=database_url))

    error_message = str(captured_error.value)

    assert database_url not in error_message
    assert "fictional-password" not in error_message
    assert isinstance(
        captured_error.value.__cause__,
        psycopg.ProgrammingError,
    )
