# backend/app/api/v1/telegram.py
from fastapi import APIRouter, HTTPException, Depends, Query, Body
from typing import List, Dict, Any, Optional
from ...services.telegram_service import TelegramService
from ...core.database import supabase_client
from ...core.config import settings
from datetime import datetime, timedelta
import logging
import traceback
import uuid
import json

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
            try:
                messages_data = await telegram_service.get_group_messages(telegram_group_id, limit=limit, save_to_db=True)
                return messages_data
            except Exception as e:
                logger.error(f"Error retrieving messages from group {telegram_group_id}: {e}")
                logger.error(traceback.format_exc())
                raise HTTPException(status_code=500, detail=f"Error fetching messages: {str(e)}")
        
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
        
        # Получаем настройки группы и список модераторов
        group_settings = group.data[0].get("settings", {})
        moderator_usernames = group_settings.get("moderators", [])
        
        if not moderator_usernames:
            logger.info(f"No moderators defined for group {group_id}")
            return []
        
        # Получаем информацию о модераторах из базы данных
        moderators = []
        for username in moderator_usernames:
            # Нормализуем имя пользователя
            if username.startswith('@'):
                username = username[1:]
                
            # Ищем пользователя в базе
            user_data = supabase_client.table('telegram_users')\
                .select('*')\
                .eq('username', username)\
                .execute()
            
            if user_data.data:
                moderator = user_data.data[0]
                moderator['is_moderator'] = True
                moderators.append(moderator)
            else:
                # Если пользователя нет в базе, добавляем базовую информацию
                moderators.append({
                    'username': username,
                    'first_name': None,
                    'last_name': None,
                    'is_moderator': True
                })
        
        logger.debug(f"Fetched {len(moderators)} moderators from database")
        return moderators
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching moderators: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/groups_add")
async def add_group(
    group_link: str,
    moderators: str = Query("", description="Comma-separated list of moderator usernames")
):
    """Добавить новую группу для отслеживания"""
    try:
        logger.debug(f"Adding new group: {group_link}")
        
        # Преобразуем строку модераторов в список
        moderator_list = []
        if moderators:
            moderator_list = [m.strip() for m in moderators.split(',') if m.strip()]
        
        # Извлекаем идентификатор группы из ссылки
        group_identifier = extract_group_identifier(group_link)
        logger.debug(f"Extracted identifier: {group_identifier}")
        
        # Получаем информацию о группе из Telegram API
        group_info = await telegram_service.get_group_info(group_identifier)
        
        if not group_info:
            logger.warning(f"Group {group_link} not found or is not accessible")
            raise HTTPException(status_code=404, detail="Group not found or is not accessible")
        
        # Проверяем, существует ли группа в базе
        existing_group = supabase_client.table('telegram_groups')\
            .select("id")\
            .eq('group_id', str(group_info['id']))\
            .execute()
        
        if existing_group.data:
            logger.warning(f"Group {group_link} already exists in database")
            return {"status": "already_exists", "group_id": existing_group.data[0]['id']}
        
        # Добавляем группу в базу с дополнительными полями
        settings = {}
        if 'settings' in group_info and isinstance(group_info['settings'], dict):
            settings = group_info['settings']
        else:
            settings = {
                'members_count': group_info.get('participants_count'),
                'username': group_info.get('username'),
                'is_public': group_info.get('is_public', False)
            }
        
        # Добавляем список модераторов в настройки
        settings['moderators'] = moderator_list
        
        new_group = {
            'group_id': str(group_info['id']),
            'name': group_info['title'],
            'link': group_link,  # Сохраняем оригинальную ссылку
            'settings': settings
        }
        
        result = supabase_client.table('telegram_groups').insert(new_group).execute()
        
        if not result.data:
            logger.error(f"Failed to add group {group_link} to database")
            raise HTTPException(status_code=500, detail="Failed to add group to database")
        
        logger.info(f"Successfully added group {group_link} to database")
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
async def analyze_group(
    group_id: str,
    analysis_params: dict = Body(...),  # Получаем параметры из тела запроса
    days_back: int = Query(7, ge=1, le=30)
):
    """Запустить анализ группы с указанными параметрами"""
    try:
        logger.info(f"Starting analysis for group {group_id}")
        
        # Извлекаем параметры из тела запроса
        prompt = analysis_params.get("prompt", "")
        moderators = analysis_params.get("moderators", [])
        days_back_param = analysis_params.get("days_back", days_back)
        
        # Логируем полученные параметры
        logger.debug(f"Analysis parameters: prompt='{prompt[:30]}...', moderators={moderators}, days_back={days_back_param}")
        
        # Проверяем, существует ли группа
        group_check = supabase_client.table('telegram_groups').select("id, name, group_id, settings").eq('id', group_id).execute()
        
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
                "sentiment_score": 78,
                "response_time_avg": 4.2,
                "resolved_issues": 35,
                "satisfaction_score": 88,
                "engagement_rate": 76,
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
            ],
            # Добавляем переданные параметры в результат для отображения в UI
            "prompt": prompt,
            "analyzed_moderators": moderators
        }
        
        # Сохраняем результаты с новыми полями
        analysis_report = {
            "group_id": group_id,
            "type": "telegram_analysis",
            "results": mock_result,
            "prompt": prompt,
            "analyzed_moderators": moderators
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
            .select("id, created_at, type, results, prompt, analyzed_moderators")\
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
            await telegram_service.connect_with_retry()
            await telegram_service.disconnect()
            return {"status": "connected", "message": "Successfully connected to Telegram API"}
        except Exception as e:
            logger.error(f"Error connecting to Telegram API: {str(e)}")
            return {"status": "error", "message": f"Error connecting to Telegram API: {str(e)}"}
    except Exception as e:
        logger.error(f"Error checking session status: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

# Управление модераторами группы
@router.post("/groups/{group_id}/moderators/{username}")
async def add_moderator(group_id: str, username: str):
    """Добавить модератора в группу"""
    try:
        # Проверяем существование группы
        group = supabase_client.table('telegram_groups').select("id, settings").eq('id', group_id).execute()
        
        if not group.data:
            logger.warning(f"Group with ID {group_id} not found")
            raise HTTPException(status_code=404, detail="Group not found")
        
        # Получаем текущие настройки группы
        group_settings = group.data[0].get("settings", {})
        
        # Получаем список модераторов
        moderators = group_settings.get("moderators", [])
        
        # Нормализуем имя пользователя
        if not username.startswith('@'):
            username = '@' + username
        
        # Проверяем, есть ли уже такой модератор
        if username in moderators:
            return {"status": "success", "message": f"Moderator {username} already exists"}
        
        # Добавляем модератора
        moderators.append(username)
        group_settings["moderators"] = moderators
        
        # Обновляем настройки группы
        supabase_client.table('telegram_groups').update({
            "settings": group_settings
        }).eq('id', group_id).execute()
        
        logger.info(f"Added moderator {username} to group {group_id}")
        return {"status": "success", "message": f"Moderator {username} added to group"}
    except Exception as e:
        logger.error(f"Error adding moderator: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/groups/{group_id}/moderators/{username}")
async def remove_moderator(group_id: str, username: str):
    """Удалить модератора из группы"""
    try:
        # Проверяем существование группы
        group = supabase_client.table('telegram_groups').select("id, settings").eq('id', group_id).execute()
        
        if not group.data:
            logger.warning(f"Group with ID {group_id} not found")
            raise HTTPException(status_code=404, detail="Group not found")
        
        # Получаем текущие настройки группы
        group_settings = group.data[0].get("settings", {})
        
        # Получаем список модераторов
        moderators = group_settings.get("moderators", [])
        
        # Нормализуем имя пользователя
        if not username.startswith('@'):
            username = '@' + username
        
        # Проверяем, есть ли такой модератор
        if username not in moderators:
            return {"status": "success", "message": f"Moderator {username} not found in group"}
        
        # Удаляем модератора
        moderators.remove(username)
        group_settings["moderators"] = moderators
        
        # Обновляем настройки группы
        supabase_client.table('telegram_groups').update({
            "settings": group_settings
        }).eq('id', group_id).execute()
        
        logger.info(f"Removed moderator {username} from group {group_id}")
        return {"status": "success", "message": f"Moderator {username} removed from group"}
    except Exception as e:
        logger.error(f"Error removing moderator: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

# Вспомогательная функция для извлечения идентификатора группы из ссылки
def extract_group_identifier(link: str) -> str:
    """Извлечь идентификатор группы из ссылки"""
    # Удаляем лишние символы
    link = link.strip()
    
    # Если это ссылка вида t.me/username или https://t.me/username
    if 't.me/' in link:
        return link.split('t.me/')[1].split('/')[0]
    
    # Если это username с @ или без
    if link.startswith('@'):
        return link[1:]
    
    # Возвращаем как есть
    return link