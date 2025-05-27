# backend/app/core/config.py
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # API
    API_V1_STR: str
    PROJECT_NAME: str
    
    # Security
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    
    # Supabase
    SUPABASE_URL: str = "https://ujtenbbwwdxclabytfws.supabase.co"
    SUPABASE_KEY: str
    # Telegram
    TELEGRAM_API_ID: int
    TELEGRAM_API_HASH: str
    TELEGRAM_SESSION_STRING: Optional[str] = None
    
    # OpenAI
    OPENAI_API_KEY: str
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()