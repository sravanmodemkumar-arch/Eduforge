from __future__ import annotations


class ExamServiceError(Exception):
    """Base exception for the Exam microservice."""

    def __init__(self, message: str = "An unexpected error occurred", status_code: int = 500) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class TestNotFoundError(ExamServiceError):
    """Raised when a requested test does not exist."""

    def __init__(self, test_id: str | None = None) -> None:
        detail = f"Test '{test_id}' not found" if test_id else "Test not found"
        super().__init__(message=detail, status_code=404)


class QuestionNotFoundError(ExamServiceError):
    """Raised when a requested question does not exist."""

    def __init__(self, question_id: str | None = None) -> None:
        detail = f"Question '{question_id}' not found" if question_id else "Question not found"
        super().__init__(message=detail, status_code=404)


class SessionNotFoundError(ExamServiceError):
    """Raised when an exam session does not exist."""

    def __init__(self, session_id: str | None = None) -> None:
        detail = f"Session '{session_id}' not found" if session_id else "Session not found"
        super().__init__(message=detail, status_code=404)


class SessionAlreadySubmittedError(ExamServiceError):
    """Raised when trying to submit an already-submitted session."""

    def __init__(self, session_id: str | None = None) -> None:
        detail = f"Session '{session_id}' has already been submitted" if session_id else "Session already submitted"
        super().__init__(message=detail, status_code=409)


class SessionExpiredError(ExamServiceError):
    """Raised when an exam session has expired."""

    def __init__(self, session_id: str | None = None) -> None:
        detail = f"Session '{session_id}' has expired" if session_id else "Session expired"
        super().__init__(message=detail, status_code=410)


class TimeWindowExceededError(ExamServiceError):
    """Raised when a submission arrives after the allowed time window (duration + grace)."""

    def __init__(self, session_id: str | None = None) -> None:
        detail = (
            f"Submission for session '{session_id}' exceeds the allowed time window"
            if session_id
            else "Submission exceeds the allowed time window"
        )
        super().__init__(message=detail, status_code=422)


class ActiveSessionExistsError(ExamServiceError):
    """Raised when a student already has an active session for the test."""

    def __init__(self) -> None:
        super().__init__(
            message="An active exam session already exists for this test",
            status_code=409,
        )


class TestNotActiveError(ExamServiceError):
    """Raised when attempting to start a session for a test that is not active/published."""

    def __init__(self, test_id: str | None = None) -> None:
        detail = f"Test '{test_id}' is not currently active" if test_id else "Test is not currently active"
        super().__init__(message=detail, status_code=403)


class InsufficientPermissionsError(ExamServiceError):
    """Raised when a user lacks the required role/permission."""

    def __init__(self, detail: str = "Insufficient permissions") -> None:
        super().__init__(message=detail, status_code=403)


class ResultNotFoundError(ExamServiceError):
    """Raised when a result record is not found."""

    def __init__(self, detail: str = "Result not found") -> None:
        super().__init__(message=detail, status_code=404)
