from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.notification import ChannelEnum, NotificationStatusEnum


# ── Send Notification ────────────────────────────────────────────────────────

class NotificationSendRequest(BaseModel):
    """Payload for sending a single notification."""

    institution_id: UUID
    recipient_id: UUID
    channel: ChannelEnum
    template_id: Optional[UUID] = None
    variables: dict[str, Any] = Field(default_factory=dict)
    # Direct content fallback when no template is used
    body: Optional[str] = None


class NotificationSendResponse(BaseModel):
    """Response after queuing a notification."""

    id: UUID
    status: NotificationStatusEnum
    message: str = "Notification queued successfully"

    model_config = {"from_attributes": True}


# ── Bulk Send ────────────────────────────────────────────────────────────────

class BulkRecipient(BaseModel):
    recipient_id: UUID
    variables: dict[str, Any] = Field(default_factory=dict)


class BulkNotificationRequest(BaseModel):
    """Payload for sending notifications to multiple recipients."""

    institution_id: UUID
    channel: ChannelEnum
    template_id: UUID
    recipients: list[BulkRecipient] = Field(..., min_length=1, max_length=1000)


class BulkNotificationResponse(BaseModel):
    """Response after queuing bulk notifications."""

    total: int
    queued: int
    failed: int
    notifications: list[NotificationSendResponse]


# ── Status / History ─────────────────────────────────────────────────────────

class NotificationStatusResponse(BaseModel):
    """Detailed status of a single notification."""

    id: UUID
    institution_id: UUID
    recipient_id: UUID
    channel: ChannelEnum
    template_id: Optional[UUID] = None
    variables: dict[str, Any] = Field(default_factory=dict)
    status: NotificationStatusEnum
    provider_message_id: Optional[str] = None
    error_message: Optional[str] = None
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class NotificationHistoryParams(BaseModel):
    """Query parameters for notification history."""

    institution_id: UUID
    recipient_id: Optional[UUID] = None
    channel: Optional[ChannelEnum] = None
    status: Optional[NotificationStatusEnum] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class NotificationHistoryResponse(BaseModel):
    """Paginated notification history."""

    items: list[NotificationStatusResponse]
    total: int
    page: int
    page_size: int
    pages: int


# ── Template Schemas ─────────────────────────────────────────────────────────

class TemplateCreateRequest(BaseModel):
    """Payload for creating a notification template."""

    name: str = Field(..., min_length=1, max_length=255)
    channel: ChannelEnum
    body_template: str = Field(..., min_length=1)
    variables_schema: dict[str, Any] = Field(default_factory=dict)
    institution_id: UUID


class TemplateUpdateRequest(BaseModel):
    """Payload for updating a notification template."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    body_template: Optional[str] = Field(None, min_length=1)
    variables_schema: Optional[dict[str, Any]] = None
    is_active: Optional[bool] = None


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
