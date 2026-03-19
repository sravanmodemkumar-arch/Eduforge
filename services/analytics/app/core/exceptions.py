"""Custom exceptions for the Analytics service."""

from fastapi import HTTPException, status


class AnalyticsServiceError(HTTPException):
    """Base exception for Analytics service errors."""

    def __init__(self, detail: str, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR) -> None:
        super().__init__(status_code=status_code, detail=detail)


class ReportNotFoundError(AnalyticsServiceError):
    """Raised when a requested report does not exist."""

    def __init__(self, report_id: str) -> None:
        super().__init__(
            detail=f"Report {report_id} not found.",
            status_code=status.HTTP_404_NOT_FOUND,
        )


class ReportGenerationError(AnalyticsServiceError):
    """Raised when report generation fails."""

    def __init__(self, report_id: str) -> None:
        super().__init__(
            detail=f"Report generation failed for {report_id}. Please retry later.",
            status_code=status.HTTP_502_BAD_GATEWAY,
        )


class UpstreamServiceError(AnalyticsServiceError):
    """Raised when an upstream microservice is unreachable or returns an error."""

    def __init__(self, service_url: str) -> None:
        super().__init__(
            detail=f"Upstream service at {service_url} is unavailable.",
            status_code=status.HTTP_502_BAD_GATEWAY,
        )
