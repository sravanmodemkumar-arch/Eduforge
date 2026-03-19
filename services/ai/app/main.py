"""EduForge AI Microservice."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from mangum import Mangum

from app.api.v1 import doubts, health, recommendations
from app.config import settings


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application startup and shutdown."""
    yield


app = FastAPI(
    title="EduForge AI Service",
    description="AI-powered doubt solving and study recommendations for EduForge",
    version="1.0.0",
    lifespan=lifespan,
    root_path=settings.root_path,
)

app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(doubts.router, prefix="/api/v1/doubts", tags=["doubts"])
app.include_router(
    recommendations.router,
    prefix="/api/v1/recommendations",
    tags=["recommendations"],
)

handler = Mangum(app, lifespan="off")
