class CollectorError(Exception):
    """Base collector exception."""


class DisabledConnectorError(CollectorError):
    """Raised when a connector is intentionally disabled."""
