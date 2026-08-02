"""Environment-backed application configuration."""

import os
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Final

from norway_job_market_intelligence.database.exceptions import (
    DatabaseConfigurationError,
)
from norway_job_market_intelligence.ingestion.exceptions import (
    NavFeedConfigurationError,
)

PROJECT_NAME: Final = "Norway Job Market Intelligence Platform"

DEFAULT_NAV_FEED_URL: Final = "https://pam-stilling-feed.nav.no/api/v1/feed"
DEFAULT_NAV_FEED_TIMEOUT_SECONDS: Final = 30.0
DEFAULT_NAV_FEED_USER_AGENT: Final = "norway-job-market-intelligence/0.1.0"


@dataclass(frozen=True, slots=True)
class DatabaseSettings:
    """Environment-backed PostgreSQL connection configuration."""

    database_url: str | None = field(default=None, repr=False)

    @classmethod
    def from_environment(
        cls,
        environment: Mapping[str, str] | None = None,
    ) -> "DatabaseSettings":
        """Load database settings without opening a connection."""

        source = os.environ if environment is None else environment

        return cls(
            database_url=_optional_environment_value(source.get("DATABASE_URL")),
        )

    def require_database_url(self) -> str:
        """Return the configured URL or raise a safe configuration error."""

        if self.database_url is None:
            raise DatabaseConfigurationError(
                "DATABASE_URL is required before database persistence."
            )

        return self.database_url


@dataclass(frozen=True, slots=True)
class NavFeedSettings:
    """Configuration required by the NAV feed HTTP client."""

    token: str | None = field(default=None, repr=False)
    feed_url: str = DEFAULT_NAV_FEED_URL
    timeout_seconds: float = DEFAULT_NAV_FEED_TIMEOUT_SECONDS
    user_agent: str = DEFAULT_NAV_FEED_USER_AGENT

    @classmethod
    def from_environment(
        cls,
        environment: Mapping[str, str] | None = None,
    ) -> "NavFeedSettings":
        """Load NAV feed settings from environment variables."""

        source = os.environ if environment is None else environment

        return cls(
            token=_optional_environment_value(source.get("NAV_FEED_TOKEN")),
            feed_url=_environment_value_or_default(
                source.get("NAV_FEED_URL"),
                DEFAULT_NAV_FEED_URL,
            ),
            timeout_seconds=_positive_float_or_default(
                variable_name="NAV_FEED_TIMEOUT_SECONDS",
                raw_value=source.get("NAV_FEED_TIMEOUT_SECONDS"),
                default=DEFAULT_NAV_FEED_TIMEOUT_SECONDS,
            ),
            user_agent=_environment_value_or_default(
                source.get("NAV_FEED_USER_AGENT"),
                DEFAULT_NAV_FEED_USER_AGENT,
            ),
        )

    def require_token(self) -> str:
        """Return the configured token or raise a safe configuration error."""

        if self.token is None:
            raise NavFeedConfigurationError(
                "NAV_FEED_TOKEN is required before requesting the NAV feed."
            )

        return self.token


def _optional_environment_value(value: str | None) -> str | None:
    if value is None:
        return None

    normalized_value = value.strip()
    return normalized_value or None


def _environment_value_or_default(
    value: str | None,
    default: str,
) -> str:
    normalized_value = _optional_environment_value(value)
    return default if normalized_value is None else normalized_value


def _positive_float_or_default(
    *,
    variable_name: str,
    raw_value: str | None,
    default: float,
) -> float:
    normalized_value = _optional_environment_value(raw_value)

    if normalized_value is None:
        return default

    try:
        parsed_value = float(normalized_value)
    except ValueError as error:
        raise NavFeedConfigurationError(f"{variable_name} must be a positive number.") from error

    if parsed_value <= 0:
        raise NavFeedConfigurationError(f"{variable_name} must be a positive number.")

    return parsed_value
