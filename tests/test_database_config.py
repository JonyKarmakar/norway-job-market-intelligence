import pytest

from norway_job_market_intelligence.config import DatabaseSettings
from norway_job_market_intelligence.database.exceptions import (
    DatabaseConfigurationError,
)


def test_database_settings_load_url_from_environment() -> None:
    settings = DatabaseSettings.from_environment(
        {
            "DATABASE_URL": (
                " postgresql://fictional-user:fictional-password@localhost:5432/fictional-database "
            )
        }
    )

    assert settings.require_database_url() == (
        "postgresql://fictional-user:fictional-password@localhost:5432/fictional-database"
    )


@pytest.mark.parametrize(
    "environment",
    [
        {},
        {"DATABASE_URL": ""},
        {"DATABASE_URL": "   "},
    ],
)
def test_missing_database_url_raises_safe_configuration_error(
    environment: dict[str, str],
) -> None:
    settings = DatabaseSettings.from_environment(environment)

    with pytest.raises(
        DatabaseConfigurationError,
        match="DATABASE_URL is required before database persistence",
    ) as captured_error:
        settings.require_database_url()

    error_message = str(captured_error.value)

    assert "fictional-password" not in error_message
    assert "postgresql://" not in error_message


def test_database_url_is_excluded_from_settings_representation() -> None:
    database_url = (
        "postgresql://fictional-user:fictional-password@localhost:5432/fictional-database"
    )

    settings = DatabaseSettings(database_url=database_url)

    assert database_url not in repr(settings)
    assert "fictional-password" not in repr(settings)
