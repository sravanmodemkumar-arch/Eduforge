"""Custom exceptions for the AI service."""

from fastapi import HTTPException, status


class AIServiceError(HTTPException):
    """Base exception for AI service errors."""

    def __init__(self, detail: str, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR) -> None:
        super().__init__(status_code=status_code, detail=detail)


class AIProcessingError(AIServiceError):
    """Raised when the AI engine fails to process a doubt."""

    def __init__(self, doubt_id: str) -> None:
        super().__init__(
            detail=f"AI processing failed for doubt {doubt_id}. Please retry later.",
            status_code=status.HTTP_502_BAD_GATEWAY,
        )


class DoubtNotFoundError(AIServiceError):
    """Raised when a requested doubt does not exist."""

    def __init__(self, doubt_id: str) -> None:
        super().__init__(
            detail=f"Doubt {doubt_id} not found.",
            status_code=status.HTTP_404_NOT_FOUND,
        )


class OpenAIConfigurationError(AIServiceError):
    """Raised when OpenAI credentials are missing or invalid."""

    def __init__(self) -> None:
        super().__init__(
            detail="OpenAI API is not configured. Contact your administrator.",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )
