# backend/app/api/v1/telegram.py
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any
from ...services.telegram_service import TelegramService
from ...core.database import supabase_client
from ...agents.telegram_agent import create_telegram_analyzer_agent
from agents import Runner
from datetime import datetime, timedelta

router = APIRouter()

@router.get("/groups")
async def get_groups():
    """Получить список отслеживаемых групп"""
    try:
        response = supabase_client.table('telegram_groups').select("*").execute()
        return response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/groups/{group_id}/analyze")
async def analyze_group(group_id: str):
    """Запустить анализ группы"""
    try:
        # Создаем агента
        agent = create_telegram_analyzer_agent()
        
        # Запускаем анализ
        result = await Runner.run(
            starting_agent=agent,
            input=f"Analyze Telegram group {group_id} and provide moderator performance metrics",
            context={"group_id": group_id}
        )
        
        # Сохраняем результаты
        await save_analysis_results(group_id, result.final_output)
        
        return {"status": "success", "result": result.final_output}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def save_analysis_results(group_id: str, results: Dict[str, Any]):
    """Сохранить результаты анализа"""
    try:
        supabase_client.table('analysis_reports').insert({
            'group_id': group_id,
            'type': 'telegram_analysis',
            'results': results
        }).execute()
    except Exception as e:
        logger.error(f"Failed to save analysis results: {e}")

@router.get("/groups/{group_id}")
async def get_group(group_id: str):
    """Получить детальную информацию о группе"""
    try:
        # Получаем информацию о группе из базы данных
        response = supabase_client.table('telegram_groups').select("*").eq('id', group_id).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Group not found")
        
        # Просто возвращаем данные группы без метрик
        return response.data[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/groups/{group_id}/messages")
async def get_group_messages(group_id: str, limit: int = 100, offset: int = 0):
    """Получить сообщения из группы"""
    try:
        # Сначала проверим существование группы
        group_response = supabase_client.table('telegram_groups').select("group_id").eq('id', group_id).execute()
        
        if not group_response.data:
            raise HTTPException(status_code=404, detail="Group not found")
            
        telegram_group_id = group_response.data[0]['group_id']
        
        # Инициализируем сервис телеграм
        telegram_service = TelegramService()
        
        # Получаем сообщения
        messages = await telegram_service.get_group_messages(telegram_group_id, limit)
        
        return messages
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/groups/{group_id}/moderators")
async def get_group_moderators(group_id: str):
    """Получить список модераторов группы"""
    try:
        # Сначала проверим существование группы
        group_response = supabase_client.table('telegram_groups').select("group_id").eq('id', group_id).execute()
        
        if not group_response.data:
            raise HTTPException(status_code=404, detail="Group not found")
            
        telegram_group_id = group_response.data[0]['group_id']
        
        # Инициализируем сервис телеграм
        telegram_service = TelegramService()
        
        # Получаем модераторов
        moderators = await telegram_service.get_moderators(telegram_group_id)
        
        return moderators
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/groups/{group_id}/messages")
async def get_group_messages(group_id: str, limit: int = 100):
    """Получить сообщения из группы"""
    try:
        # Проверяем существование группы
        group = supabase_client.table('telegram_groups').select("*").eq('id', group_id).execute()
        
        if not group.data:
            raise HTTPException(status_code=404, detail="Group not found")
        
        # Получаем сообщения из базы
        messages = supabase_client.table('telegram_messages')\
            .select("*")\
            .eq('group_id', group_id)\
            .order('date', desc=True)\
            .limit(limit)\
            .execute()
        
        return messages.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/groups/{group_id}/moderators")
async def get_group_moderators(group_id: str):
    """Получить модераторов группы"""
    try:
        # Проверяем существование группы
        group = supabase_client.table('telegram_groups').select("*").eq('id', group_id).execute()
        
        if not group.data:
            raise HTTPException(status_code=404, detail="Group not found")
        
        # Для тестирования возвращаем тестовые данные
        # В реальной системе здесь будет запрос к базе данных
        return [
            {
                "id": "1",
                "telegram_id": "123456789",
                "username": "admin_user",
                "first_name": "Admin",
                "last_name": "User",
                "is_moderator": True
            },
            {
                "id": "2",
                "telegram_id": "987654321",
                "username": "moderator_user",
                "first_name": "Moderator",
                "last_name": "Assistant",
                "is_moderator": True
            }
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/groups/{group_id}/collect")
async def collect_group_data(group_id: str, limit: int = 100):
    """Собрать данные группы и сохранить в базу"""
    try:
        # Проверяем существование группы
        group = supabase_client.table('telegram_groups').select("*").eq('id', group_id).execute()
        
        if not group.data:
            raise HTTPException(status_code=404, detail="Group not found")
        
        # Получаем Telegram ID группы
        telegram_group_id = group.data[0]["group_id"]
        
        # Инициализируем сервис Telegram
        telegram_service = TelegramService()
        
        # Собираем данные
        result = await telegram_service.collect_group_data(telegram_group_id, messages_limit=limit)
        
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/groups/{group_id}/analyze")
async def analyze_group(group_id: str):
    """Запустить анализ группы"""
    try:
        # Для тестирования возвращаем мок-результаты
        mock_result = {
            "sentiment_score": 78,
            "response_time": "4.2 min",
            "resolved_issues": 35,
            "satisfaction_score": "88%",
            "engagement_rate": "76%",
            "key_topics": ["support", "feedback", "technical issues", "updates"]
        }
        
        # Сохраняем результаты
        analysis_report = {
            "group_id": group_id,
            "type": "telegram_analysis",
            "date_from": (datetime.now() - timedelta(days=7)).isoformat(),
            "date_to": datetime.now().isoformat(),
            "results": mock_result
        }
        
        supabase_client.table('analysis_reports').insert(analysis_report).execute()
        
        return {"status": "success", "result": mock_result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))