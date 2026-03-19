"""SQLAlchemy 2.0 async base configuration."""

from __future__ import annotations

import os
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Uuid, func
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
)

# ---------------------------------------------------------------------------
# Engine / session helpers
# ---------------------------------------------------------------------------

_default_engine = None
_default_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_async_engine(database_url: str | None = None):
    """Return (and cache) an asyncpg-backed async engine.

    If *database_url* is ``None`` the ``DATABASE_URL`` environment variable is
    used.  The URL must use the ``postgresql+asyncpg://`` scheme.
    """
    global _default_engine
    if _default_engine is None:
        url = database_url or os.environ["DATABASE_URL"]
        _default_engine = create_async_engine(
            url,
            echo=False,
            pool_size=20,
            max_overflow=10,
            pool_pre_ping=True,
        )
    return _default_engine


def _get_session_factory() -> async_sessionmaker[AsyncSession]:
    global _default_session_factory
    if _default_session_factory is None:
        engine = get_async_engine()
        _default_session_factory = async_sessionmaker(
            bind=engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _default_session_factory


async def get_async_session():
    """FastAPI dependency that yields an ``AsyncSession``.

    Usage::

        @router.get("/items")
        async def list_items(session: AsyncSession = Depends(get_async_session)):
            ...
    """
    factory = _get_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# ---------------------------------------------------------------------------
# Declarative base with common columns
# ---------------------------------------------------------------------------


class Base(DeclarativeBase):
    """Shared declarative base for all EduForge models."""

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


# ---------------------------------------------------------------------------
# Mixins
# ---------------------------------------------------------------------------


class TimestampMixin:
    """Mixin that adds ``created_at`` and ``updated_at`` columns."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class TenantMixin:
    """Mixin that adds an ``institution_id`` foreign-key column.

    The FK target (``institutions.id``) lives in the ``iam`` schema and is
    expected to exist when the migration runs.
    """

    institution_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        nullable=False,
        index=True,
    )
