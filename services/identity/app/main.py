from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum

from app.api.v1 import auth, health, institutions, users
from app.core.database import engine, Base
from app.core.exceptions import register_exception_handlers


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create tables if needed (use Alembic in production)
    async with engine.begin() as conn:
        await conn.execute(
            __import__("sqlalchemy").text("CREATE SCHEMA IF NOT EXISTS identity")
        )
    yield
    # Shutdown: dispose engine
    await engine.dispose()


app = FastAPI(
    title="EduForge Identity Service",
    description="Authentication, authorization, and identity management for EduForge platform",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(institutions.router)
app.include_router(health.router)

# AWS Lambda handler via Mangum
handler = Mangum(app, lifespan="off")
