# backend/app/main.py
from fastapi import FastAPI
from .api.v1 import telegram, moderators, analytics, auth
from .core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Убираем CORS middleware для упрощения

# Включаем роутеры
app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])
app.include_router(telegram.router, prefix=f"{settings.API_V1_STR}/telegram", tags=["telegram"])
app.include_router(moderators.router, prefix=f"{settings.API_V1_STR}/moderators", tags=["moderators"])
app.include_router(analytics.router, prefix=f"{settings.API_V1_STR}/analytics", tags=["analytics"])

@app.get("/")
async def root():
    return {"message": "Multi-Channel Analyzer API"}