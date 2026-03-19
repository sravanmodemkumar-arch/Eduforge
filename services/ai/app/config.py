"""Application configuration loaded from environment variables."""

from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """AI service settings."""

    # Application
    app_name: str = "eduforge-ai"
    debug: bool = False
    root_path: str = ""

    # Database
    database_url: str = (
        "postgresql+asyncpg://postgres:postgres@localhost:5432/eduforge"
    )

    # OpenAI
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"
    openai_max_tokens: int = 2048
    openai_temperature: float = 0.3

    # R2 / S3
    r2_endpoint_url: str = ""
    r2_access_key_id: str = ""
    r2_secret_access_key: str = ""
    r2_bucket_name: str = "eduforge-ai"

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
