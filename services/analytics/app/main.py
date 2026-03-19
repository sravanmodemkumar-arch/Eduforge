"""EduForge Analytics Microservice."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from mangum import Mangum

from app.api.v1 import dashboards, health, reports
from app.config import settings


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application startup and shutdown."""
    yield


app = FastAPI(
    title="EduForge Analytics Service",
    description="Reporting and dashboard analytics for EduForge institutions",
    version="1.0.0",
    lifespan=lifespan,
    root_path=settings.root_path,
)

app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(reports.router, prefix="/api/v1/reports", tags=["reports"])
app.include_router(dashboards.router, prefix="/api/v1/dashboards", tags=["dashboards"])

handler = Mangum(app, lifespan="off")
