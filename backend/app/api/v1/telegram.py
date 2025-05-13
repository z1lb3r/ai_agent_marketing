# backend/app/api/v1/telegram.py
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any
from ...services.telegram_service import TelegramService
from ...core.database import supabase_client
# from ...agents.telegram_agent import create_telegram_analyzer_agent
# from agents import Runner
from datetime import datetime, timedelta
import logging
import traceback

router = APIRouter()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

@router.get("/groups")
async def get_groups():
    """Получить список отслеживаемых групп"""
    try:
        logger.debug("Fetching telegram groups from Supabase")
        response = supabase_client.table('telegram_groups').select("*").execute()
        logger.debug(f"Fetched {len(response.data)} groups")
        return response.data
    except Exception as e:
        logger.error(f"Error fetching groups: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/groups/{group_id}")
async def get_group(group_id: str):
    """Получить детальную информацию о группе"""
    try:
        logger.debug(f"Fetching details for group {group_id}")
        # Получаем информацию о группе из базы данных
        response = supabase_client.table('telegram_groups').select("*").eq('id', group_id).execute()
        
        if not response.data:
            logger.warning(f"Group with ID {group_id} not found")
            raise HTTPException(status_code=404, detail="Group not found")
        
        logger.debug(f"Successfully fetched details for group {group_id}")
        # Просто возвращаем данные группы без метрик
        return response.data[0]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching group details: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/groups/{group_id}/messages")
async def get_group_messages(group_id: str, limit: int = 100):
    """Получить сообщения из группы"""
    try:
        logger.debug(f"Fetching messages for group {group_id} with limit {limit}")
        # Проверяем существование группы
        group = supabase_client.table('telegram_groups').select("*").eq('id', group_id).execute()
        
        if not group.data:
            logger.warning(f"Group with ID {group_id} not found")
            raise HTTPException(status_code=404, detail="Group not found")
        
        logger.debug(f"Group found, fetching messages")
        # Получаем сообщения из базы
        messages = supabase_client.table('telegram_messages')\
            .select("*")\
            .eq('group_id', group_id)\
            .order('date', desc=True)\
            .limit(limit)\
            .execute()
        
        logger.debug(f"Fetched {len(messages.data)} messages")
        return messages.data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching messages: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/groups/{group_id}/moderators")
async def get_group_moderators(group_id: str):
    """Получить модераторов группы"""
    try:
        logger.debug(f"Fetching moderators for group {group_id}")
        # Проверяем существование группы
        group = supabase_client.table('telegram_groups').select("*").eq('id', group_id).execute()
        
        if not group.data:
            logger.warning(f"Group with ID {group_id} not found")
            raise HTTPException(status_code=404, detail="Group not found")
        
        logger.debug("Returning mock moderators data")
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
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching moderators: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/groups/{group_id}/collect")
async def collect_group_data(group_id: str, limit: int = 100):
    """Собрать данные группы и сохранить в базу"""
    try:
        logger.debug(f"Starting data collection for group {group_id} with limit {limit}")
        # Проверяем существование группы
        group = supabase_client.table('telegram_groups').select("*").eq('id', group_id).execute()
        
        if not group.data:
            logger.warning(f"Group with ID {group_id} not found")
            raise HTTPException(status_code=404, detail="Group not found")
        
        # Получаем Telegram ID группы
        telegram_group_id = group.data[0]["group_id"]
        logger.debug(f"Group found with Telegram ID: {telegram_group_id}")
        
        # Инициализируем сервис Telegram
        logger.debug("Initializing Telegram service")
        telegram_service = TelegramService()
        
        # Собираем данные
        logger.debug(f"Collecting data from Telegram group {telegram_group_id}")
        try:
            result = await telegram_service.collect_group_data(telegram_group_id, messages_limit=limit)
            logger.debug("Data collection completed successfully")
        except Exception as telegram_error:
            logger.error(f"Error collecting data from Telegram: {str(telegram_error)}")
            logger.error(traceback.format_exc())
            raise HTTPException(status_code=500, detail=f"Telegram data collection failed: {str(telegram_error)}")
        
        return {"status": "success", "data": result}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during data collection: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/groups/{group_id}/analyze")
async def analyze_group(group_id: str):
    """Запустить анализ группы"""
    try:
        logger.info(f"Starting analysis for group {group_id}")
        
        # Проверяем, существует ли группа
        logger.debug(f"Checking if group {group_id} exists")
        group_check = supabase_client.table('telegram_groups').select("id, name").eq('id', group_id).execute()
        
        if not group_check.data or len(group_check.data) == 0:
            logger.warning(f"Group with ID {group_id} not found")
            raise HTTPException(status_code=404, detail="Group not found")
        
        group_name = group_check.data[0].get("name", "Unknown")
        logger.debug(f"Group found: {group_name}")
        
        # Создаем расширенные мок-результаты анализа
        logger.debug("Generating mock analysis results")
        mock_result = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "sentiment_score": 78,  # 0-100 scale
                "response_time_avg": 4.2,  # minutes
                "resolved_issues": 35,
                "satisfaction_score": 88,  # 0-100 scale
                "engagement_rate": 76,  # 0-100 scale
            },
            "key_topics": ["support", "feedback", "technical issues", "updates"],
            "moderator_metrics": {
                "response_time": {
                    "avg": 4.2,
                    "min": 0.5,
                    "max": 12.3
                },
                "sentiment": {
                    "positive": 65,
                    "neutral": 25,
                    "negative": 10
                },
                "performance": {
                    "effectiveness": 82,
                    "helpfulness": 85,
                    "clarity": 78
                }
            },
            "recommendations": [
                "Улучшить время ответа в периоды высокой активности",
                "Обратить внимание на более детальные ответы по техническим вопросам",
                "Продолжать поддерживать позитивный тон в общении"
            ]
        }
        
        # Сохраняем результаты с правильными полями
        logger.debug("Preparing data for insertion into analysis_reports table")
        analysis_report = {
            "group_id": group_id,
            "type": "telegram_analysis",
            "results": mock_result
            # created_at будет добавлено автоматически
        }
        
        # Логируем данные перед вставкой
        logger.debug("Inserting analysis results into database")
        try:
            result = supabase_client.table('analysis_reports').insert(analysis_report).execute()
            logger.debug("Successfully inserted analysis results")
        except Exception as db_error:
            logger.error(f"Database error: {str(db_error)}")
            logger.error(traceback.format_exc())
            # Продолжаем выполнение, чтобы вернуть данные пользователю, даже если сохранение не удалось
            logger.warning("Returning analysis results without saving to database")
            return {"status": "partial_success", "message": "Analysis completed but results not saved", "result": mock_result}
        
        logger.info(f"Analysis for group {group_id} completed successfully")
        return {"status": "success", "result": mock_result}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during analysis: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

async def save_analysis_results(group_id: str, results: Dict[str, Any]):
    """Сохранить результаты анализа"""
    try:
        logger.debug(f"Saving analysis results for group {group_id}")
        supabase_client.table('analysis_reports').insert({
            'group_id': group_id,
            'type': 'telegram_analysis',
            'results': results
        }).execute()
        logger.debug("Analysis results saved successfully")
    except Exception as e:
        logger.error(f"Failed to save analysis results: {e}")
        logger.error(traceback.format_exc())
        raise Exception(f"Failed to save analysis results: {e}")