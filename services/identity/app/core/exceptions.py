from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class AppException(Exception):
    """Base application exception."""

    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class OTPExpiredError(AppException):
    def __init__(self, message: str = "OTP has expired"):
        super().__init__(message=message, status_code=400)


class OTPInvalidError(AppException):
    def __init__(self, message: str = "Invalid OTP"):
        super().__init__(message=message, status_code=400)


class RateLimitExceededError(AppException):
    def __init__(self, message: str = "Too many OTP requests. Please try again later."):
        super().__init__(message=message, status_code=429)


class InstitutionNotFoundError(AppException):
    def __init__(self, message: str = "Institution not found"):
        super().__init__(message=message, status_code=404)


class UserNotFoundError(AppException):
    def __init__(self, message: str = "User not found"):
        super().__init__(message=message, status_code=404)


class AuthenticationError(AppException):
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message=message, status_code=401)


class AuthorizationError(AppException):
    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(message=message, status_code=403)


class SessionExpiredError(AppException):
    def __init__(self, message: str = "Session has expired"):
        super().__init__(message=message, status_code=401)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": type(exc).__name__,
                "message": exc.message,
                "status_code": exc.status_code,
            },
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content={
                "error": "InternalServerError",
                "message": "An unexpected error occurred",
                "status_code": 500,
            },
        )
