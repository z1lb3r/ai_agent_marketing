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
        
    def init_tables(self):
        """Инициализация таблиц если они не существуют"""
        logger.info("Начинаем инициализацию таблиц...")
        
        try:
            # Вывести сведения о подключении для проверки
            logger.info(f"Используем Supabase URL: {settings.SUPABASE_URL}")
            
            # Создаем таблицу telegram_groups через SQL
            result = self.client.sql("""
                CREATE TABLE IF NOT EXISTS telegram_groups (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    group_id VARCHAR NOT NULL,
                    name VARCHAR NOT NULL,
                    settings JSONB DEFAULT '{}'::jsonb,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                );
            """).execute()
            
            logger.info(f"SQL-запрос выполнен для telegram_groups: {result}")
            
            # Создаем таблицу analysis_reports через SQL
            result = self.client.sql("""
                CREATE TABLE IF NOT EXISTS analysis_reports (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    group_id VARCHAR NOT NULL,
                    type VARCHAR NOT NULL,
                    results JSONB NOT NULL,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                );
            """).execute()
            
            logger.info(f"SQL-запрос выполнен для analysis_reports: {result}")
            
            # Проверка создания таблиц
            tables = self.client.table('information_schema.tables').select('*').execute()
            logger.info(f"Доступные таблицы: {tables.data}")
            
        except Exception as e:
            logger.error(f"Ошибка при инициализации таблиц: {e}")
            import traceback
            logger.error(traceback.format_exc())

# Глобальный экземпляр
supabase_client = SupabaseClient().db