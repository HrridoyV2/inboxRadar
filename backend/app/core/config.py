from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
# In Docker, the .env might be in /app if copied, or we rely on env vars from docker-compose
ENV_FILE_PATH = ROOT_DIR / ".env"
if not ENV_FILE_PATH.exists():
    # Try /app/.env as a fallback for certain docker setups
    alt_path = Path("/app/.env")
    if alt_path.exists():
        ENV_FILE_PATH = alt_path

class Settings(BaseSettings):
    # Environment
    APP_ENV: str = Field("development", alias="APP_ENV")

    # Database
    DATABASE_URL: str = Field(..., alias="DATABASE_URL")
    SUPABASE_URL: Optional[str] = Field(None, alias="SUPABASE_URL")
    SUPABASE_ANON_KEY: Optional[str] = Field(None, alias="SUPABASE_ANON_KEY")

    # Supabase Frontend
    NEXT_PUBLIC_SUPABASE_URL: Optional[str] = Field(None, alias="NEXT_PUBLIC_SUPABASE_URL")
    NEXT_PUBLIC_SUPABASE_ANON_KEY: Optional[str] = Field(None, alias="NEXT_PUBLIC_SUPABASE_ANON_KEY")

    # Email Receiver (IMAP)
    MOCK_MODE: bool = Field(True, alias="MOCK_MODE")
    IMAP_SERVER: str = Field("imap.gmail.com", alias="IMAP_SERVER")
    EMAIL_USER: str = Field(..., alias="EMAIL_USER")
    EMAIL_PASS: str = Field(..., alias="EMAIL_PASS")

    # Email Sender (SMTP)
    SMTP_SERVER: str = Field("smtp.gmail.com", alias="SMTP_SERVER")
    SMTP_SENDER_EMAIL: str = Field(..., alias="SMTP_SENDER_EMAIL")
    SMTP_SENDER_PASS: str = Field(..., alias="SMTP_SENDER_PASS")

    # AI
    GEMINI_API_KEY: str = Field(..., alias="GEMINI_API_KEY")

    # Frontend / API
    NEXT_PUBLIC_API_URL: str = Field("http://localhost:8000", alias="NEXT_PUBLIC_API_URL")
    FRONTEND_TARGET: str = Field("deps", alias="FRONTEND_TARGET")

    # Security
    JWT_SECRET: str = Field("inboxradar-fallback-secret-key-change-me", alias="JWT_SECRET")

    # CORS
    ALLOWED_CORS_ORIGINS: str = Field("*", alias="ALLOWED_CORS_ORIGINS")

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE_PATH),
        env_file_encoding="utf-8",
        extra="ignore",
    )

settings = Settings()
