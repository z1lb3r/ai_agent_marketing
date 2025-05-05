from fastapi import APIRouter, HTTPException
from ...core.database import supabase_client

router = APIRouter()

@router.get("/connection")
async def test_connection():
    """Проверка соединения с Supabase"""
    try:
        # Проверяем соединение, запрашивая список таблиц
        result = supabase_client.from_('telegram_groups').select('*').limit(1).execute()
        return {
            "status": "success",
            "message": "Соединение с Supabase установлено",
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка соединения с Supabase: {str(e)}")