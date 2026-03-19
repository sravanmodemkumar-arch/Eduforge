from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Exam microservice configuration."""

    # ── Application ──────────────────────────────────────────────────────
    APP_NAME: str = "EduForge Exam Service"
    DEBUG: bool = False
    ENVIRONMENT: str = "production"

    # ── Database ─────────────────────────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/eduforge"
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10
    DB_SCHEMA: str = "exam"

    # ── Cloudflare R2 / S3-compatible storage ────────────────────────────
    R2_ENDPOINT_URL: str = ""
    R2_ACCESS_KEY_ID: str = ""
    R2_SECRET_ACCESS_KEY: str = ""
    R2_BUCKET_NAME: str = "eduforge-exams"
    R2_REGION: str = "auto"

    # ── CDN ──────────────────────────────────────────────────────────────
    CDN_BASE_URL: str = "https://cdn.eduforge.io/exams"

    # ── AWS SQS ──────────────────────────────────────────────────────────
    SQS_QUEUE_URL: str = ""
    SQS_NOTIFICATION_QUEUE_URL: str = ""
    AWS_REGION: str = "ap-south-1"
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""

    # ── JWT ──────────────────────────────────────────────────────────────
    JWT_SECRET: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_AUDIENCE: str = "eduforge"
    JWT_ISSUER: str = "eduforge-auth"

    # ── Exam defaults ────────────────────────────────────────────────────
    SESSION_GRACE_PERIOD_SECONDS: int = 60

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
    }


@lru_cache
def get_settings() -> Settings:
    return Settings()
