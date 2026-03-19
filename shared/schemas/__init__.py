"""Common Pydantic v2 schemas shared across microservices."""

from shared.schemas.common import (
    ResponseSchema,
    PaginatedResponse,
    ErrorResponse,
    HealthResponse,
)

__all__ = [
    "ResponseSchema",
    "PaginatedResponse",
    "ErrorResponse",
    "HealthResponse",
]
