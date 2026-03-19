"""Billing service configuration."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="BILLING_",
        case_sensitive=False,
    )

    # ── FastAPI ──────────────────────────────────────────────────────────
    app_name: str = "EduForge Billing Service"
    debug: bool = False

    # ── Database ─────────────────────────────────────────────────────────
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/eduforge"
    db_pool_size: int = 10
    db_max_overflow: int = 20
    db_schema: str = "billing"

    # ── Razorpay ─────────────────────────────────────────────────────────
    razorpay_key_id: str = ""
    razorpay_key_secret: str = ""
    razorpay_webhook_secret: str = ""

    # ── GST ──────────────────────────────────────────────────────────────
    gst_rate: float = 0.18  # 18%
    cgst_rate: float = 0.09  # 9%
    sgst_rate: float = 0.09  # 9%
    igst_rate: float = 0.18  # 18%
    seller_gstin: str = ""
    seller_state_code: str = ""
    default_sac_code: str = "9993"

    # ── AWS / R2 ─────────────────────────────────────────────────────────
    s3_endpoint_url: str = ""
    s3_bucket_name: str = "eduforge-invoices"
    s3_access_key_id: str = ""
    s3_secret_access_key: str = ""
    s3_region: str = "auto"

    # ── Service URLs ─────────────────────────────────────────────────────
    auth_service_url: str = "http://localhost:8000"


settings = Settings()
