"""Billing service FastAPI application entry point."""

from __future__ import annotations

from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI
from mangum import Mangum

from app.config import settings
from app.core.database import engine, get_db  # noqa: F401 – re-exported for endpoint imports


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan: initialise and tear down resources."""
    yield
    await engine.dispose()


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    lifespan=lifespan,
)

# ── Register routers ─────────────────────────────────────────────────────
from app.api.v1.health import router as health_router  # noqa: E402
from app.api.v1.payments import router as payments_router  # noqa: E402
from app.api.v1.subscriptions import router as subscriptions_router  # noqa: E402
from app.api.v1.invoices import router as invoices_router  # noqa: E402

app.include_router(health_router, prefix="/api/v1")
app.include_router(payments_router, prefix="/api/v1")
app.include_router(subscriptions_router, prefix="/api/v1")
app.include_router(invoices_router, prefix="/api/v1")

# ── AWS Lambda handler ───────────────────────────────────────────────────
handler = Mangum(app, lifespan="off")
