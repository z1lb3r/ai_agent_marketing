# backend/app/core/config.py
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # API
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Multi-Channel Analyzer"
    
    # Security
    SECRET_KEY: str = "IKxvqKwYH4_fRPKzHFhm3B33XxKbEWZK9JTZwbgb5zI"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    
    # Supabase
    SUPABASE_URL: str = "https://ujtenbbwwdxclabytfws.supabase.co"
    SUPABASE_KEY: str = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVqdGVuYmJ3d2R4Y2xhYnl0ZndzIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0NjI5NjM4MCwiZXhwIjoyMDYxODcyMzgwfQ.bYf3kL1eWlP-GcGHeXkNcZ8cKEG-CP1ig1btZJrhRA8"#"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVqdGVuYmJ3d2R4Y2xhYnl0ZndzIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDYyOTYzODAsImV4cCI6MjA2MTg3MjM4MH0.DH6EKY52XbxKEgbv215s976MphAu5BmhwNJ2bbipmfM"
    
    # Telegram
    TELEGRAM_API_ID: int = 26178048
    TELEGRAM_API_HASH: str = "633cb5646d9e16fcc51d3115326a8ff7"
    TELEGRAM_SESSION_STRING: Optional[str] = None
    
    # OpenAI
    OPENAI_API_KEY: str = "sk-proj-3LWBvkxjChcDTQt66JZsEn7ttoCFk_5Gj59I7sLcT-KZ-WY6R7fb80KzgCDOUYvRD4EjNImkYqT3BlbkFJnXVt6U3LFWq4XJuivu7s0W0IzEKbtEt1bFH7_lSMRhoMPSd-FxJHqpvvVPPYb-rgvDmfbnfoVEA"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()