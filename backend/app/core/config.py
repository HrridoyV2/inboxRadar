import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    APP_ENV: str = "development"
    
    # Database Configuration
    DATABASE_URL: str = Field(..., alias="DATABASE_URL")
    SUPABASE_URL: Optional[str] = None
    SUPABASE_ANON_KEY: Optional[str] = None
    
    # Email Polling & Simulation Settings
    MOCK_MODE: bool = True
    IMAP_SERVER: str = "imap.gmail.com"
    EMAIL_USER: str = "alex142nomad@gmail.com"
    EMAIL_PASS: str = "feufgbcyyyxvbdkl"

    # SMTP Sender Credentials (Trigger 2)
    SMTP_SENDER_EMAIL: str = "adrijroy99@gmail.com"
    SMTP_SENDER_PASS: str = "qmme iemy wvpj znhp"
    
    # Gemini AI Key
    GEMINI_API_KEY: Optional[str] = None
    
    # API Settings
    NEXT_PUBLIC_API_URL: str = "http://localhost:8000/api"
    FRONTEND_TARGET: str = "deps"
    
    # Security Settings
    JWT_SECRET: str = "inboxradar-jwt-secret-key-super-secure"
    ALLOWED_CORS_ORIGINS: str = "https://inboxradar.mutho.tech,http://localhost:3000,http://127.0.0.1:3000,http://localhost:3001,http://127.0.0.1:3001"

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
