from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Notification service configuration."""

    # ── Application ──────────────────────────────────────────────────────
    APP_NAME: str = "EduForge Notification Service"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # ── Database ─────────────────────────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/notification"
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10
    DB_ECHO: bool = False

    # ── WhatsApp (Meta Business API) ─────────────────────────────────────
    WHATSAPP_API_URL: str = "https://graph.facebook.com/v18.0"
    WHATSAPP_PHONE_NUMBER_ID: str = ""
    WHATSAPP_ACCESS_TOKEN: str = ""
    WHATSAPP_VERIFY_TOKEN: str = ""

    # ── SMS (MSG91) ──────────────────────────────────────────────────────
    MSG91_API_URL: str = "https://control.msg91.com/api/v5"
    MSG91_AUTH_KEY: str = ""
    MSG91_SENDER_ID: str = ""
    MSG91_DLT_TE_ID: Optional[str] = None

    # ── Email (SendGrid) ─────────────────────────────────────────────────
    SENDGRID_API_KEY: str = ""
    SENDGRID_FROM_EMAIL: str = "noreply@eduforge.io"
    SENDGRID_FROM_NAME: str = "EduForge"

    # ── Push Notifications (Firebase) ────────────────────────────────────
    FIREBASE_CREDENTIALS_PATH: str = ""
    FIREBASE_PROJECT_ID: str = ""

    # ── AWS / SQS ────────────────────────────────────────────────────────
    AWS_REGION: str = "ap-south-1"
    SQS_QUEUE_URL: str = ""
    SQS_MAX_MESSAGES: int = 10
    SQS_WAIT_TIME_SECONDS: int = 20
    SQS_VISIBILITY_TIMEOUT: int = 60

    # ── Rate Limiting ────────────────────────────────────────────────────
    RATE_LIMIT_PER_INSTITUTION: int = 1000
    RATE_LIMIT_WINDOW_SECONDS: int = 3600

    # ── Retry ────────────────────────────────────────────────────────────
    MAX_RETRIES: int = 3
    RETRY_BACKOFF_SECONDS: float = 2.0

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
    }


@lru_cache()
def get_settings() -> Settings:
    """Return cached settings singleton."""
    return Settings()
