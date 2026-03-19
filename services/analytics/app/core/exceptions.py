from fastapi import HTTPException, status


class ReportNotFoundError(HTTPException):
    def __init__(self, report_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report {report_id} not found",
        )


class ReportGenerationError(HTTPException):
    def __init__(self, message: str = "Failed to generate report"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=message,
        )
