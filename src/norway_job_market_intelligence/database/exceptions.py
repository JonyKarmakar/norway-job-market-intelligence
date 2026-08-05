"""Safe project-level exceptions for database operations."""


class DatabaseError(Exception):
    """Base exception for database configuration and persistence failures."""


class DatabaseConfigurationError(DatabaseError):
    """Raised when required database configuration is unavailable."""


class DatabaseConnectionError(DatabaseError):
    """Raised when a PostgreSQL connection cannot be established safely."""


class SourceEventPersistenceError(DatabaseError):
    """Raised when a NAV source event cannot be persisted."""


class CurrentAdvertisementPersistenceError(DatabaseError):
    """Raised when current NAV advertisement state cannot be maintained."""
