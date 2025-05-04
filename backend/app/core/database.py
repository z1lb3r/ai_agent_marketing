# backend/app/core/database.py
from supabase import create_client, Client
from .config import settings
import logging

logger = logging.getLogger(__name__)

class SupabaseClient:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            try:
                cls._instance.client = create_client(
                    settings.SUPABASE_URL,
                    settings.SUPABASE_KEY
                )
                logger.info("Successfully connected to Supabase")
            except Exception as e:
                logger.error(f"Failed to connect to Supabase: {e}")
                raise
        return cls._instance
    
    @property
    def db(self) -> Client:
        return self.client

# Глобальный экземпляр
supabase_client = SupabaseClient().db