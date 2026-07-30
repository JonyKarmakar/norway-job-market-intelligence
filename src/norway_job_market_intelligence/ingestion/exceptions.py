"""Project-level exceptions for NAV feed ingestion."""


class NavFeedError(Exception):
    """Base exception for NAV feed client and payload-processing failures."""


class NavFeedConfigurationError(NavFeedError):
    """Raised when required NAV feed configuration is unavailable or invalid."""


class NavFeedAuthenticationError(NavFeedError):
    """Raised when NAV rejects authentication or authorization."""


class NavFeedRequestError(NavFeedError):
    """Raised when an HTTP request cannot be completed successfully."""


class NavFeedInvalidJsonError(NavFeedError):
    """Raised when a NAV response does not contain valid JSON."""


class NavFeedStructureError(NavFeedError):
    """Raised when a NAV response has an unexpected structure."""


class PrivacyValidationError(NavFeedError):
    """Raised when a payload cannot satisfy the project privacy boundary."""
