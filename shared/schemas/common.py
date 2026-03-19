"""Common Pydantic v2 response models used across all EduForge services."""

from __future__ import annotations

from typing import Any, Generic, Sequence, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ResponseSchema(BaseModel, Generic[T]):
    """Standard envelope for successful API responses."""

    success: bool = True
    message: str = "OK"
    data: T | None = None


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated list response."""

    items: Sequence[T]
    total: int
    page: int = Field(ge=1)
    page_size: int = Field(ge=1)


class ErrorResponse(BaseModel):
    """Standard error response body."""

    detail: str
    error_code: str | None = None


class HealthResponse(BaseModel):
    """Health-check response returned by every microservice."""

    status: str = "ok"
    service: str
    version: str
