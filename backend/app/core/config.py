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
    
    # Gemini AI Key
    GEMINI_API_KEY: Optional[str] = None
    
    # API Settings
    NEXT_PUBLIC_API_URL: str = "http://localhost:8000/api"
    FRONTEND_TARGET: str = "deps"

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
