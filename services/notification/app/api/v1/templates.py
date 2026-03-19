"""Notification template management endpoints."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.models.notification import ChannelEnum
from app.schemas.template import (
    TemplateCreateRequest,
    TemplateListResponse,
    TemplateResponse,
    TemplateUpdateRequest,
)
from app.services.notification_service import NotificationService

router = APIRouter()


def _get_service() -> NotificationService:
    return NotificationService()


@router.post(
    "/",
    response_model=TemplateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create notification template",
)
async def create_template(
    payload: TemplateCreateRequest,
    service: NotificationService = Depends(_get_service),
) -> TemplateResponse:
    """Create a new notification template (OTP, result, fee reminder, attendance alert)."""
    return await service.create_template(payload)


@router.get(
    "/",
    response_model=TemplateListResponse,
    summary="List templates",
)
async def list_templates(
    institution_id: UUID = Query(..., description="Institution UUID"),
    channel: ChannelEnum | None = Query(None, description="Filter by channel"),
    is_active: bool | None = Query(None, description="Filter by active status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: NotificationService = Depends(_get_service),
) -> TemplateListResponse:
    """List notification templates for an institution with optional filters."""
    return await service.list_templates(
        institution_id=institution_id,
        channel=channel,
        is_active=is_active,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{template_id}",
    response_model=TemplateResponse,
    summary="Get template details",
)
async def get_template(
    template_id: UUID,
    service: NotificationService = Depends(_get_service),
) -> TemplateResponse:
    """Retrieve a single template by ID."""
    result = await service.get_template(template_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template {template_id} not found",
        )
    return result


@router.put(
    "/{template_id}",
    response_model=TemplateResponse,
    summary="Update template",
)
async def update_template(
    template_id: UUID,
    payload: TemplateUpdateRequest,
    service: NotificationService = Depends(_get_service),
) -> TemplateResponse:
    """Update an existing notification template."""
    result = await service.update_template(template_id, payload)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template {template_id} not found",
        )
    return result


@router.delete(
    "/{template_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete template",
)
async def delete_template(
    template_id: UUID,
    service: NotificationService = Depends(_get_service),
) -> None:
    """Soft-delete a template by deactivating it."""
    success = await service.delete_template(template_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template {template_id} not found",
        )
