"""Async session management with per-schema search_path support."""

from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


async def set_search_path(session: AsyncSession, schema_name: str) -> None:
    """Set the PostgreSQL ``search_path`` for the given session.

    This ensures that all subsequent queries within the session resolve
    unqualified table names against *schema_name*.
    """
    await session.execute(text(f"SET search_path TO {schema_name}, public"))


class AsyncSessionManager:
    """Manage one async engine + session factory per database schema.

    Usage::

        manager = AsyncSessionManager("postgresql+asyncpg://…")
        async with manager.session("course_svc") as session:
            ...
    """

    def __init__(self, database_url: str, **engine_kwargs) -> None:
        defaults = {
            "echo": False,
            "pool_size": 20,
            "max_overflow": 10,
            "pool_pre_ping": True,
        }
        defaults.update(engine_kwargs)
        self._engine: AsyncEngine = create_async_engine(database_url, **defaults)
        self._factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
            bind=self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
        self._schemas: dict[str, bool] = {}

    @property
    def engine(self) -> AsyncEngine:
        return self._engine

    class _SessionContext:
        """Async context manager that yields a session with search_path set."""

        def __init__(
            self,
            factory: async_sessionmaker[AsyncSession],
            schema_name: str,
        ) -> None:
            self._factory = factory
            self._schema_name = schema_name
            self._session: AsyncSession | None = None

        async def __aenter__(self) -> AsyncSession:
            self._session = self._factory()
            await set_search_path(self._session, self._schema_name)
            return self._session

        async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
            assert self._session is not None
            try:
                if exc_type is None:
                    await self._session.commit()
                else:
                    await self._session.rollback()
            finally:
                await self._session.close()

    def session(self, schema_name: str) -> _SessionContext:
        """Return an async context manager that provides a session scoped to *schema_name*."""
        return self._SessionContext(self._factory, schema_name)

    async def close(self) -> None:
        """Dispose of the underlying engine and its connection pool."""
        await self._engine.dispose()
