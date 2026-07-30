import pytest

from norway_job_market_intelligence.config import (
    DEFAULT_NAV_FEED_TIMEOUT_SECONDS,
    DEFAULT_NAV_FEED_URL,
    DEFAULT_NAV_FEED_USER_AGENT,
    NavFeedSettings,
)
from norway_job_market_intelligence.ingestion.exceptions import (
    NavFeedConfigurationError,
)


def test_settings_load_token_from_environment() -> None:
    settings = NavFeedSettings.from_environment({"NAV_FEED_TOKEN": " fictional-token "})

    assert settings.require_token() == "fictional-token"


def test_settings_use_documented_defaults() -> None:
    settings = NavFeedSettings.from_environment({})

    assert settings.feed_url == DEFAULT_NAV_FEED_URL
    assert settings.timeout_seconds == DEFAULT_NAV_FEED_TIMEOUT_SECONDS
    assert settings.user_agent == DEFAULT_NAV_FEED_USER_AGENT


def test_settings_load_optional_environment_values() -> None:
    settings = NavFeedSettings.from_environment(
        {
            "NAV_FEED_TOKEN": "fictional-token",
            "NAV_FEED_URL": "https://example.invalid/feed",
            "NAV_FEED_TIMEOUT_SECONDS": "12.5",
            "NAV_FEED_USER_AGENT": "njmi-tests/1.0",
        }
    )

    assert settings.feed_url == "https://example.invalid/feed"
    assert settings.timeout_seconds == 12.5
    assert settings.user_agent == "njmi-tests/1.0"


def test_missing_token_raises_safe_configuration_error() -> None:
    settings = NavFeedSettings.from_environment({})

    with pytest.raises(
        NavFeedConfigurationError,
        match="NAV_FEED_TOKEN is required",
    ) as captured_error:
        settings.require_token()

    assert "Bearer" not in str(captured_error.value)
    assert "fictional-token" not in str(captured_error.value)


def test_token_is_excluded_from_settings_representation() -> None:
    token = "fictional-secret-token"
    settings = NavFeedSettings(token=token)

    assert token not in repr(settings)


@pytest.mark.parametrize(
    "timeout_value",
    ["0", "-1", "not-a-number"],
)
def test_invalid_timeout_raises_configuration_error(
    timeout_value: str,
) -> None:
    with pytest.raises(
        NavFeedConfigurationError,
        match="NAV_FEED_TIMEOUT_SECONDS must be a positive number",
    ):
        NavFeedSettings.from_environment({"NAV_FEED_TIMEOUT_SECONDS": timeout_value})
