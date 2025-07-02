# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.v1 import telegram, moderators, analytics, auth, client_monitoring
from .core.config import settings
from .core.database import supabase_client
from .services.telegram_service import TelegramService
from .services.scheduler_service import scheduler_service
import asyncio
import logging

# Настройка логирования
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Включаем роутеры
app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])
app.include_router(telegram.router, prefix=f"{settings.API_V1_STR}/telegram", tags=["telegram"])
app.include_router(moderators.router, prefix=f"{settings.API_V1_STR}/moderators", tags=["moderators"])
app.include_router(analytics.router, prefix=f"{settings.API_V1_STR}/analytics", tags=["analytics"])

# НОВЫЙ РОУТЕР: Мониторинг клиентов
app.include_router(client_monitoring.router, prefix=f"{settings.API_V1_STR}/client-monitoring", tags=["client-monitoring"])

# Безопасный startup event
@app.on_event("startup")
async def startup_event():
    logger.info("Starting Multi-Channel Analyzer API...")
    
    # Запускаем планировщик задач для мониторинга клиентов
    try:
        scheduler_service.start()
        logger.info("Scheduler started successfully")
    except Exception as e:
        logger.error(f"Failed to start scheduler: {e}")
    
    logger.info("Application started successfully. Telegram client will be initialized on demand.")

# Корректное закрытие приложения
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down application...")
    
    # Останавливаем планировщик
    try:
        scheduler_service.stop()
        logger.info("Scheduler stopped successfully")
    except Exception as e:
        logger.error(f"Error stopping scheduler: {e}")
    
    # Останавливаем Telegram клиент
    telegram_service = TelegramService()
    try:
        await asyncio.wait_for(telegram_service.close(), timeout=5.0)
        logger.info("Telegram client closed successfully")
    except asyncio.TimeoutError:
        logger.warning("Timeout occurred while closing Telegram client, forcing shutdown")
    except Exception as e:
        logger.error(f"Error closing Telegram client: {e}")
    
    # Явно очищаем ресурсы
    if hasattr(telegram_service, 'client') and telegram_service.client:
        telegram_service.client = None

@app.get("/")
async def root():
    return {"message": "Multi-Channel Analyzer API with Client Monitoring"}

# Новый endpoint для проверки статуса мониторинга
@app.get("/health/monitoring")
async def monitoring_health():
    """Проверка состояния системы мониторинга"""
    try:
        # Проверяем подключение к БД
        result = supabase_client.table('monitoring_settings').select('count').execute()
        
        # Проверяем планировщик
        scheduler_running = scheduler_service.scheduler.running if scheduler_service.scheduler else False
        
        return {
            "status": "healthy",
            "database": "connected",
            "scheduler": "running" if scheduler_running else "stopped",
            "timestamp": asyncio.get_event_loop().time()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": asyncio.get_event_loop().time()
        }