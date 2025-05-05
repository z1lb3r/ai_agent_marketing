# test_insert.py
from fastapi import FastAPI
from supabase import create_client
from pydantic import BaseModel
import uvicorn

app = FastAPI()

# Подключение к Supabase
supabase_url = "https://ujtenbbwwdxclabytfws.supabase.co"
supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVqdGVuYmJ3d2R4Y2xhYnl0ZndzIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDYyOTYzODAsImV4cCI6MjA2MTg3MjM4MH0.DH6EKY52XbxKEgbv215s976MphAu5BmhwNJ2bbipmfM"
supabase = create_client(supabase_url, supabase_key)

# Модель данных
class TelegramGroup(BaseModel):
    group_id: str
    name: str
    settings: dict = {}

@app.get("/add-test-group")
def add_test_group():
    # Тестовые данные
    test_group = {
        "group_id": "test123456",
        "name": "Test Group",
        "settings": {
            "members_count": 150,
            "is_active": True
        }
    }
    
    try:
        # Добавление данных в таблицу
        response = supabase.table('telegram_groups').insert(test_group).execute()
        
        # Проверка результата
        return {
            "status": "success",
            "message": "Тестовая группа добавлена",
            "data": response.data
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Ошибка при добавлении данных: {str(e)}"
        }

@app.get("/test-groups")
def get_test_groups():
    try:
        # Получение данных из таблицы
        response = supabase.table('telegram_groups').select('*').execute()
        return {
            "status": "success",
            "count": len(response.data),
            "data": response.data
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Ошибка при получении данных: {str(e)}"
        }

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8001)