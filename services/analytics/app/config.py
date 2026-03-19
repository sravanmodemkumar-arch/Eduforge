"""Application configuration loaded from environment variables."""

from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Analytics service settings."""

    # Application
    app_name: str = "eduforge-analytics"
    debug: bool = False
    root_path: str = ""

    # Database
    database_url: str = (
        "postgresql+asyncpg://postgres:postgres@localhost:5432/eduforge"
    )

    # R2 / S3 – used for storing generated report files
    r2_endpoint_url: str = ""
    r2_access_key_id: str = ""
    r2_secret_access_key: str = ""
    r2_bucket_name: str = "eduforge-reports"

    # Internal service URLs
    attendance_service_url: str = "http://localhost:8004"
    assessment_service_url: str = "http://localhost:8005"
    fee_service_url: str = "http://localhost:8003"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()


settings = get_settings()
