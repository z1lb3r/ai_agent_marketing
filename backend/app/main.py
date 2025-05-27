# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.v1 import telegram, moderators, analytics, auth
from .core.config import settings
from .services.telegram_service import TelegramService
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

# Безопасный startup event без блокирующих операций
@app.on_event("startup")
async def startup_event():
    logger.info("Starting Multi-Channel Analyzer API...")
    logger.info("Application started successfully. Telegram client will be initialized on demand.")

# Корректное закрытие клиента при остановке приложения
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down application...")
    telegram_service = TelegramService()
    try:
        # Установим таймаут на закрытие соединения
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
    return {"message": "Multi-Channel Analyzer API"}


# Закомментированный старый код для справки:
"""
# Инициализация Telegram клиента при запуске приложения - ОТКЛЮЧЕНО
@app.on_event("startup")
async def startup_event():
    logger.info("Starting application...")
    telegram_service = TelegramService()
    try:
        await telegram_service.start()  # ЭТА СТРОКА БЛОКИРОВАЛА ЗАПУСК
        logger.info("Telegram client started successfully")
    except Exception as e:
        logger.error(f"Error starting Telegram client: {e}")
        logger.warning("Application will continue, but Telegram functionality may be limited")
"""