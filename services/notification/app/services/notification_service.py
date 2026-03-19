"""Orchestrates notification sending, status tracking, and template management."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.config import get_settings
from app.core.exceptions import (
    NotificationError,
    ProviderError,
    TemplateNotFoundError,
)
from app.models.notification import ChannelEnum, Notification, NotificationStatusEnum
from app.models.template import Template
from app.providers.email import EmailProvider
from app.providers.push import PushProvider
from app.providers.sms import SMSProvider
from app.providers.whatsapp import WhatsAppProvider
from app.schemas.notification import (
    BulkNotificationRequest,
    BulkNotificationResponse,
    NotificationHistoryResponse,
    NotificationSendRequest,
    NotificationSendResponse,
    NotificationStatusResponse,
)
from app.schemas.template import (
    TemplateCreateRequest,
    TemplateListResponse,
    TemplateResponse,
    TemplateUpdateRequest,
)

logger = logging.getLogger(__name__)

# ── Lazy session factory ─────────────────────────────────────────────────────
_async_session_factory: sessionmaker | None = None


def _get_session_factory() -> sessionmaker:
    global _async_session_factory
    if _async_session_factory is None:
        settings = get_settings()
        engine = create_async_engine(
            settings.DATABASE_URL,
            pool_size=settings.DB_POOL_SIZE,
            max_overflow=settings.DB_MAX_OVERFLOW,
            echo=settings.DB_ECHO,
        )
        _async_session_factory = sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )
    return _async_session_factory


class NotificationService:
    """Orchestrates notification sending across all channels."""

    def __init__(self, db: AsyncSession | None = None) -> None:
        self._db = db
        self._providers: dict[ChannelEnum, Any] = {
            ChannelEnum.WHATSAPP: WhatsAppProvider(),
            ChannelEnum.SMS: SMSProvider(),
            ChannelEnum.EMAIL: EmailProvider(),
            ChannelEnum.PUSH: PushProvider(),
        }

    async def _get_db(self) -> AsyncSession:
        """Return the injected session or create one from the factory."""
        if self._db is not None:
            return self._db
        factory = _get_session_factory()
        self._db = factory()
        return self._db

    # ── Send single notification ─────────────────────────────────────────

    async def send(self, request: NotificationSendRequest) -> NotificationSendResponse:
        """Queue and dispatch a single notification."""
        db = await self._get_db()
        body = request.body

        # Resolve template if provided
        if request.template_id:
            body = await self._resolve_template(request.template_id, request.variables)

        if not body:
            raise NotificationError("Either template_id or body must be provided")

        notification = Notification(
            id=uuid.uuid4(),
            institution_id=request.institution_id,
            recipient_id=request.recipient_id,
            channel=request.channel,
            template_id=request.template_id,
            variables=request.variables,
            status=NotificationStatusEnum.QUEUED,
        )
        db.add(notification)
        await db.flush()

        # Attempt delivery
        await self._dispatch(notification, body)
        await db.commit()

        return NotificationSendResponse(
            id=notification.id,
            status=notification.status,
            message=(
                "Notification sent successfully"
                if notification.status == NotificationStatusEnum.SENT
                else "Notification queued successfully"
            ),
        )

    # ── Bulk send ────────────────────────────────────────────────────────

    async def send_bulk(
        self, request: BulkNotificationRequest
    ) -> BulkNotificationResponse:
        """Queue and dispatch notifications to multiple recipients."""
        db = await self._get_db()
        body = await self._resolve_template(request.template_id, {})
        results: list[NotificationSendResponse] = []
        failed = 0

        for recipient in request.recipients:
            rendered = self._render_body(body, recipient.variables)
            notification = Notification(
                id=uuid.uuid4(),
                institution_id=request.institution_id,
                recipient_id=recipient.recipient_id,
                channel=request.channel,
                template_id=request.template_id,
                variables=recipient.variables,
                status=NotificationStatusEnum.QUEUED,
            )
            db.add(notification)
            await db.flush()

            try:
                await self._dispatch(notification, rendered)
            except Exception:
                failed += 1
                logger.exception("Failed to send notification %s", notification.id)

            results.append(
                NotificationSendResponse(
                    id=notification.id,
                    status=notification.status,
                )
            )

        await db.commit()

        queued = len(results) - failed
        return BulkNotificationResponse(
            total=len(results),
            queued=queued,
            failed=failed,
            notifications=results,
        )

    # ── Status ───────────────────────────────────────────────────────────

    async def get_status(
        self, notification_id: uuid.UUID
    ) -> NotificationStatusResponse | None:
        """Retrieve the current status of a notification."""
        db = await self._get_db()
        result = await db.execute(
            select(Notification).where(Notification.id == notification_id)
        )
        notification = result.scalar_one_or_none()
        if notification is None:
            return None
        return NotificationStatusResponse.model_validate(notification)

    # ── History ──────────────────────────────────────────────────────────

    async def get_history(
        self,
        institution_id: uuid.UUID,
        recipient_id: uuid.UUID | None = None,
        channel: ChannelEnum | None = None,
        status: NotificationStatusEnum | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> NotificationHistoryResponse:
        """Return paginated notification history with optional filters."""
        db = await self._get_db()
        query = select(Notification).where(
            Notification.institution_id == institution_id
        )

        if recipient_id is not None:
            query = query.where(Notification.recipient_id == recipient_id)
        if channel is not None:
            query = query.where(Notification.channel == channel)
        if status is not None:
            query = query.where(Notification.status == status)

        # Total count
        count_query = select(func.count()).select_from(query.subquery())
        total = (await db.execute(count_query)).scalar() or 0

        # Paginate
        offset = (page - 1) * page_size
        query = (
            query.order_by(Notification.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        result = await db.execute(query)
        items = [
            NotificationStatusResponse.model_validate(n)
            for n in result.scalars().all()
        ]

        pages = max(1, (total + page_size - 1) // page_size)
        return NotificationHistoryResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )

    # ── Template CRUD ────────────────────────────────────────────────────

    async def create_template(self, request: TemplateCreateRequest) -> TemplateResponse:
        """Create a new notification template."""
        db = await self._get_db()
        template = Template(
            id=uuid.uuid4(),
            name=request.name,
            channel=request.channel,
            body_template=request.body_template,
            variables_schema=request.variables_schema,
            institution_id=request.institution_id,
            is_active=True,
        )
        db.add(template)
        await db.commit()
        await db.refresh(template)
        return TemplateResponse.model_validate(template)

    async def list_templates(
        self,
        institution_id: uuid.UUID,
        channel: ChannelEnum | None = None,
        is_active: bool | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> TemplateListResponse:
        """List notification templates for an institution with pagination."""
        db = await self._get_db()
        query = select(Template).where(Template.institution_id == institution_id)

        if channel is not None:
            query = query.where(Template.channel == channel)
        if is_active is not None:
            query = query.where(Template.is_active == is_active)

        # Total count
        count_query = select(func.count()).select_from(query.subquery())
        total = (await db.execute(count_query)).scalar() or 0

        # Paginate
        offset = (page - 1) * page_size
        query = query.order_by(Template.created_at.desc()).offset(offset).limit(page_size)
        result = await db.execute(query)
        items = [TemplateResponse.model_validate(t) for t in result.scalars().all()]

        pages = max(1, (total + page_size - 1) // page_size)
        return TemplateListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )

    async def get_template(self, template_id: uuid.UUID) -> TemplateResponse | None:
        """Retrieve a single template by ID."""
        db = await self._get_db()
        result = await db.execute(select(Template).where(Template.id == template_id))
        template = result.scalar_one_or_none()
        if template is None:
            return None
        return TemplateResponse.model_validate(template)

    async def update_template(
        self, template_id: uuid.UUID, request: TemplateUpdateRequest
    ) -> TemplateResponse | None:
        """Update an existing template. Returns None if not found."""
        db = await self._get_db()
        result = await db.execute(select(Template).where(Template.id == template_id))
        template = result.scalar_one_or_none()
        if template is None:
            return None

        update_data = request.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(template, field, value)

        await db.commit()
        await db.refresh(template)
        return TemplateResponse.model_validate(template)

    async def delete_template(self, template_id: uuid.UUID) -> bool:
        """Soft-delete a template by deactivating it. Returns False if not found."""
        db = await self._get_db()
        result = await db.execute(select(Template).where(Template.id == template_id))
        template = result.scalar_one_or_none()
        if template is None:
            return False

        template.is_active = False
        await db.commit()
        return True

    # ── Internal helpers ─────────────────────────────────────────────────

    async def _resolve_template(
        self,
        template_id: uuid.UUID,
        variables: dict[str, Any],
    ) -> str:
        """Load a template and render it with the given variables."""
        db = await self._get_db()
        result = await db.execute(
            select(Template).where(
                Template.id == template_id, Template.is_active.is_(True)
            )
        )
        template = result.scalar_one_or_none()
        if template is None:
            raise TemplateNotFoundError(
                f"Template {template_id} not found or inactive"
            )
        return self._render_body(template.body_template, variables)

    @staticmethod
    def _render_body(body_template: str, variables: dict[str, Any]) -> str:
        """Replace {{key}} placeholders with variable values."""
        rendered = body_template
        for key, value in variables.items():
            rendered = rendered.replace(f"{{{{{key}}}}}", str(value))
        return rendered

    async def _dispatch(self, notification: Notification, body: str) -> None:
        """Send the notification through the appropriate channel provider."""
        provider = self._providers.get(notification.channel)
        if provider is None:
            notification.status = NotificationStatusEnum.FAILED
            notification.error_message = (
                f"No provider configured for channel {notification.channel}"
            )
            return

        try:
            provider_message_id = await provider.send(
                recipient_id=str(notification.recipient_id),
                body=body,
                variables=notification.variables or {},
            )
            notification.status = NotificationStatusEnum.SENT
            notification.provider_message_id = provider_message_id
            notification.sent_at = datetime.now(timezone.utc)
        except ProviderError as exc:
            logger.error(
                "Provider error for notification %s: %s",
                notification.id,
                exc,
            )
            notification.status = NotificationStatusEnum.FAILED
            notification.error_message = str(exc)
        except Exception as exc:
            logger.exception(
                "Unexpected error dispatching notification %s",
                notification.id,
            )
            notification.status = NotificationStatusEnum.FAILED
            notification.error_message = f"Unexpected error: {exc}"
