class NotificationServiceError(Exception):
    """Base exception for the notification service."""

    def __init__(self, message: str = "An error occurred in the notification service") -> None:
        self.message = message
        super().__init__(self.message)


class NotificationError(NotificationServiceError):
    """Raised when a notification cannot be created or processed."""


class TemplateNotFoundError(NotificationServiceError):
    """Raised when a referenced template does not exist or is inactive."""


class TemplateRenderError(NotificationServiceError):
    """Raised when template rendering fails due to missing variables."""


class ProviderError(NotificationServiceError):
    """Raised when an external provider (WhatsApp, SMS, Email, Push) fails."""


class RateLimitExceededError(NotificationServiceError):
    """Raised when an institution exceeds its notification rate limit."""


class InvalidRecipientError(NotificationServiceError):
    """Raised when the recipient identifier is invalid for the given channel."""


class ConfigurationError(NotificationServiceError):
    """Raised when required configuration is missing or invalid."""
