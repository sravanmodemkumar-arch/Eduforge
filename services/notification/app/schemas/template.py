"""Pydantic schemas for notification templates."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.notification import ChannelEnum


class TemplateCreateRequest(BaseModel):
    """Payload for creating a notification template."""

    name: str = Field(..., min_length=1, max_length=255)
    channel: ChannelEnum
    body_template: str = Field(..., min_length=1)
    variables_schema: dict[str, Any] = Field(default_factory=dict)
    institution_id: UUID


class TemplateUpdateRequest(BaseModel):
    """Payload for updating a notification template."""

    name: str | None = Field(None, min_length=1, max_length=255)
    body_template: str | None = Field(None, min_length=1)
    variables_schema: dict[str, Any] | None = None
    is_active: bool | None = None


class TemplateResponse(BaseModel):
    """Template detail response."""

    id: UUID
    name: str
    channel: ChannelEnum
    body_template: str
    variables_schema: dict[str, Any]
    institution_id: UUID
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class TemplateListResponse(BaseModel):
    """Paginated list of templates."""

    items: list[TemplateResponse]
    total: int
    page: int
    page_size: int
    pages: int
