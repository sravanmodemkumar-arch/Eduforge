from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/eduforge"

    # JWT
    JWT_SECRET_KEY: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # WhatsApp OTP
    WHATSAPP_API_URL: str = ""
    WHATSAPP_API_TOKEN: str = ""

    # MSG91 SMS fallback
    MSG91_API_KEY: str = ""
    MSG91_SENDER_ID: str = "EDUFGE"

    # OTP
    OTP_EXPIRE_SECONDS: int = 300

    # Cloudflare R2
    R2_ENDPOINT_URL: str = ""
    R2_ACCESS_KEY_ID: str = ""
    R2_SECRET_ACCESS_KEY: str = ""
    R2_BUCKET_NAME: str = "eduforge"

    # AWS SQS
    SQS_QUEUE_URL: str = ""
    SQS_REGION: str = "ap-south-1"
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""


settings = Settings()
