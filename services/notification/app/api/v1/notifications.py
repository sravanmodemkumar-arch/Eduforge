"""Notification sending and status endpoints."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.models.notification import ChannelEnum, NotificationStatusEnum
from app.schemas.notification import (
    BulkNotificationRequest,
    BulkNotificationResponse,
    NotificationHistoryResponse,
    NotificationSendRequest,
    NotificationSendResponse,
    NotificationStatusResponse,
)
from app.services.notification_service import NotificationService

router = APIRouter()


def _get_service() -> NotificationService:
    return NotificationService()


@router.post(
    "/send",
    response_model=NotificationSendResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Send a single notification",
)
async def send_notification(
    payload: NotificationSendRequest,
    service: NotificationService = Depends(_get_service),
) -> NotificationSendResponse:
    """Queue a notification for delivery via the specified channel."""
    return await service.send(payload)


@router.post(
    "/bulk",
    response_model=BulkNotificationResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Bulk send notifications (e.g. result day for 74K students)",
)
async def send_bulk_notifications(
    payload: BulkNotificationRequest,
    service: NotificationService = Depends(_get_service),
) -> BulkNotificationResponse:
    """Queue bulk notifications for delivery. Designed for high-volume events
    like result publication day (~74K students).
    """
    return await service.send_bulk(payload)


@router.get(
    "/{notification_id}/status",
    response_model=NotificationStatusResponse,
    summary="Get notification delivery status",
)
async def get_notification_status(
    notification_id: UUID,
    service: NotificationService = Depends(_get_service),
) -> NotificationStatusResponse:
    """Retrieve current delivery status for a notification."""
    result = await service.get_status(notification_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Notification {notification_id} not found",
        )
    return result


@router.get(
    "/history",
    response_model=NotificationHistoryResponse,
    summary="Notification history with filters",
)
async def get_notification_history(
    institution_id: UUID = Query(..., description="Institution UUID"),
    recipient_id: UUID | None = Query(None, description="Recipient UUID"),
    channel: ChannelEnum | None = Query(None, description="Notification channel"),
    notification_status: NotificationStatusEnum | None = Query(
        None, alias="status", description="Notification status"
    ),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    service: NotificationService = Depends(_get_service),
) -> NotificationHistoryResponse:
    """Retrieve paginated notification history for an institution."""
    return await service.get_history(
        institution_id=institution_id,
        recipient_id=recipient_id,
        channel=channel,
        status=notification_status,
        page=page,
        page_size=page_size,
    )
