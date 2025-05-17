# backend/app/api/v1/telegram.py
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Dict, Any, Optional
from ...services.telegram_service import TelegramService
from ...core.database import supabase_client
from ...core.config import settings
from datetime import datetime, timedelta
import logging
import traceback
import uuid

router = APIRouter()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Telegram service initialization
telegram_service = TelegramService()


@router.get("/groups")
async def get_groups():
    try:
        logger.debug("Fetching telegram groups from Supabase")
        # Подробное логирование
        logger.debug(f"Supabase URL: {settings.SUPABASE_URL}")
        logger.debug(f"Using table: telegram_groups")
        
        response = supabase_client.table('telegram_groups').select("*").execute()
        
        # Логируем полный ответ
        logger.debug(f"Supabase response: {response}")
        
        # Проверяем, есть ли данные
        if not response.data:
            logger.warning("No groups found in the database")
        
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
        return response.data[0]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching group details: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/groups/{group_id}/messages")
async def get_group_messages(group_id: str, limit: int = Query(100, ge=1, le=1000)):
    """Получить сообщения из группы"""
    try:
        logger.debug(f"Fetching messages for group {group_id} with limit {limit}")
        # Проверяем существование группы
        group = supabase_client.table('telegram_groups').select("*").eq('id', group_id).execute()
        
        if not group.data:
            logger.warning(f"Group with ID {group_id} not found")
            raise HTTPException(status_code=404, detail="Group not found")
        
        # Получаем телеграм ID группы
        telegram_group_id = group.data[0]["group_id"]
        
        # Сначала пробуем получить сообщения из базы данных
        messages = supabase_client.table('telegram_messages')\
            .select("*")\
            .eq('group_id', group_id)\
            .order('date', desc=True)\
            .limit(limit)\
            .execute()
        
        # Если в базе нет сообщений, получаем их из Telegram API
        if not messages.data:
            logger.debug(f"No messages found in database, fetching from Telegram API")
            messages_data = await telegram_service.get_group_messages(telegram_group_id, limit=limit, save_to_db=True)
            return messages_data
        
        logger.debug(f"Fetched {len(messages.data)} messages from database")
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
        
        telegram_group_id = group.data[0]["group_id"]
        
        # Пробуем получить модераторов из базы данных
        moderators = supabase_client.table('telegram_users')\
            .select("*")\
            .eq('is_moderator', True)\
            .execute()
        
        # Если в базе нет модераторов или их меньше 2, получаем их из Telegram API
        if not moderators.data or len(moderators.data) < 2:
            logger.debug(f"Few or no moderators found in database, fetching from Telegram API")
            moderators_data = await telegram_service.get_moderators(telegram_group_id, save_to_db=True)
            return moderators_data
        
        logger.debug(f"Fetched {len(moderators.data)} moderators from database")
        return moderators.data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching moderators: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/groups_add")
async def add_group(group_username: str):
    """Добавить новую группу для отслеживания"""
    try:
        logger.debug(f"Adding new group: {group_username}")
        
        # Получаем информацию о группе из Telegram API
        group_info = await telegram_service.get_group_info(group_username)
        
        if not group_info:
            logger.warning(f"Group {group_username} not found or is not accessible")
            raise HTTPException(status_code=404, detail="Group not found or is not accessible")
        
        # Проверяем, существует ли группа в базе
        existing_group = supabase_client.table('telegram_groups')\
            .select("id")\
            .eq('group_id', group_info['id'])\
            .execute()
        
        if existing_group.data:
            logger.warning(f"Group {group_username} already exists in database")
            return {"status": "already_exists", "group_id": existing_group.data[0]['id']}
        
        # Добавляем группу в базу
        new_group = {
            'group_id': group_info['id'],
            'name': group_info['title'],
            'settings': {
                'members_count': group_info.get('participants_count'),
                'username': group_info.get('username'),
                'is_public': group_info.get('is_public', False)
            }
        }
        
        result = supabase_client.table('telegram_groups').insert(new_group).execute()
        
        if not result.data:
            logger.error(f"Failed to add group {group_username} to database")
            raise HTTPException(status_code=500, detail="Failed to add group to database")
        
        logger.info(f"Successfully added group {group_username} to database")
        return {"status": "success", "group_id": result.data[0]['id']}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding group: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/groups/{group_id}/collect")
async def collect_group_data(group_id: str, limit: int = Query(100, ge=1, le=1000)):
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
        
        # Собираем данные из Telegram
        try:
            result = await telegram_service.collect_group_data(telegram_group_id, messages_limit=limit)
            logger.debug("Data collection completed successfully")
            return {"status": "success", "data": result}
        except Exception as telegram_error:
            logger.error(f"Error collecting data from Telegram: {str(telegram_error)}")
            logger.error(traceback.format_exc())
            raise HTTPException(status_code=500, detail=f"Telegram data collection failed: {str(telegram_error)}")
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
        group_check = supabase_client.table('telegram_groups').select("id, name, group_id").eq('id', group_id).execute()
        
        if not group_check.data or len(group_check.data) == 0:
            logger.warning(f"Group with ID {group_id} not found")
            raise HTTPException(status_code=404, detail="Group not found")
        
        group_name = group_check.data[0].get("name", "Unknown")
        telegram_group_id = group_check.data[0].get("group_id")
        logger.debug(f"Group found: {group_name}")
        
        # Пока используем мок-результаты анализа
        # В дальнейшем здесь будет интеграция с OpenAI API
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

@router.get("/groups/{group_id}/analytics")
async def get_group_analytics(group_id: str):
    """Получить результаты последнего анализа группы"""
    try:
        logger.debug(f"Fetching analytics for group {group_id}")
        
        # Проверяем существование группы
        group = supabase_client.table('telegram_groups').select("id").eq('id', group_id).execute()
        
        if not group.data:
            logger.warning(f"Group with ID {group_id} not found")
            raise HTTPException(status_code=404, detail="Group not found")
        
        # Получаем последний отчет анализа из базы данных
        analysis_reports = supabase_client.table('analysis_reports')\
            .select("*")\
            .eq('group_id', group_id)\
            .order('created_at', desc=True)\
            .limit(1)\
            .execute()
        
        if not analysis_reports.data:
            logger.warning(f"No analysis reports found for group {group_id}")
            return {"status": "not_found", "message": "No analysis reports available for this group"}
        
        logger.debug(f"Successfully fetched analytics for group {group_id}")
        return {"status": "success", "result": analysis_reports.data[0]['results']}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching analytics: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/groups/{group_id}/history")
async def get_analysis_history(
    group_id: str, 
    limit: int = Query(10, ge=1, le=100),
    from_date: Optional[str] = None,
    to_date: Optional[str] = None
):
    """Получить историю результатов анализа группы"""
    try:
        logger.debug(f"Fetching analysis history for group {group_id}")
        
        # Проверяем существование группы
        group = supabase_client.table('telegram_groups').select("id").eq('id', group_id).execute()
        
        if not group.data:
            logger.warning(f"Group with ID {group_id} not found")
            raise HTTPException(status_code=404, detail="Group not found")
        
        # Формируем запрос к базе данных
        query = supabase_client.table('analysis_reports')\
            .select("id, created_at, type, results")\
            .eq('group_id', group_id)
        
        # Добавляем фильтры по датам если указаны
        if from_date:
            query = query.gte('created_at', from_date)
        if to_date:
            query = query.lte('created_at', to_date)
            
        # Выполняем запрос
        reports = query.order('created_at', desc=True).limit(limit).execute()
        
        if not reports.data:
            logger.warning(f"No analysis history found for group {group_id}")
            return {"status": "not_found", "message": "No analysis history available for this group"}
        
        logger.debug(f"Successfully fetched {len(reports.data)} analysis reports for group {group_id}")
        return {"status": "success", "results": reports.data}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching analysis history: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/messages/{message_id}/thread")
async def get_message_thread(message_id: str, group_id: str):
    """Получить ветку сообщений"""
    try:
        logger.debug(f"Fetching thread for message {message_id} in group {group_id}")
        
        # Проверяем существование группы
        group = supabase_client.table('telegram_groups').select("*").eq('id', group_id).execute()
        
        if not group.data:
            logger.warning(f"Group with ID {group_id} not found")
            raise HTTPException(status_code=404, detail="Group not found")
        
        telegram_group_id = group.data[0]["group_id"]
        
        # Получаем сообщение из базы
        message = supabase_client.table('telegram_messages')\
            .select("*")\
            .eq('group_id', group_id)\
            .eq('message_id', message_id)\
            .execute()
        
        if not message.data:
            logger.warning(f"Message with ID {message_id} not found")
            raise HTTPException(status_code=404, detail="Message not found")
        
        # Получаем ветку сообщений из Telegram API
        thread_messages = await telegram_service.get_message_thread(
            telegram_group_id, 
            int(message_id), 
            limit=50
        )
        
        logger.debug(f"Successfully fetched thread with {len(thread_messages)} messages")
        return thread_messages
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching message thread: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/session")
async def get_session_status():
    """Проверить статус сессии Telegram"""
    try:
        # Проверяем, есть ли сессия
        if not settings.TELEGRAM_SESSION_STRING:
            return {"status": "not_configured", "message": "Telegram session string is not configured"}
        
        # Пробуем подключиться к Telegram
        try:
            await telegram_service.connect()
            await telegram_service.disconnect()
            return {"status": "connected", "message": "Successfully connected to Telegram API"}
        except Exception as e:
            logger.error(f"Error connecting to Telegram API: {str(e)}")
            return {"status": "error", "message": f"Error connecting to Telegram API: {str(e)}"}
    except Exception as e:
        logger.error(f"Error checking session status: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))
                    