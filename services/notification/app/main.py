from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum

from app.api.v1 import health, notifications, templates
from app.config import get_settings

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    yield


app = FastAPI(
    title="EduForge Notification Service",
    description="Multi-channel notification delivery: WhatsApp, SMS, Email, Push",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, tags=["health"])
app.include_router(
    notifications.router,
    prefix="/api/v1/notifications",
    tags=["notifications"],
)
app.include_router(
    templates.router,
    prefix="/api/v1/templates",
    tags=["templates"],
)

handler = Mangum(app, lifespan="off")
