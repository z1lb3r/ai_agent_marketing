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
import asyncio

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
    analysis_params: dict = Body(...),
    days_back: int = Query(7, ge=1, le=30)
):
    """Запустить РЕАЛЬНЫЙ анализ группы через OpenAI"""
    try:
        logger.info(f"Starting OpenAI analysis for group {group_id}")
        
        # Извлекаем параметры
        prompt = analysis_params.get("prompt", "")
        moderators = analysis_params.get("moderators", [])
        days_back_param = analysis_params.get("days_back", days_back)
        
        if not prompt.strip():
            raise HTTPException(status_code=400, detail="Prompt is required for analysis")
        
        # Проверяем группу
        group_check = supabase_client.table('telegram_groups').select("*").eq('id', group_id).execute()
        
        if not group_check.data:
            raise HTTPException(status_code=404, detail="Group not found")
        
        group_data = group_check.data[0]
        group_name = group_data.get("name", "Unknown")
        telegram_group_id = group_data.get("group_id")
        
        # Получаем реальные сообщения из группы
        messages = await telegram_service.get_group_messages(
            telegram_group_id, 
            limit=200,  # Увеличиваем лимит для лучшего анализа
            get_users=True
        )
        
        if not messages:
            raise HTTPException(status_code=400, detail="No messages found in group for analysis")
        
        logger.info(f"Analyzing {len(messages)} messages with OpenAI")
        
        # РЕАЛЬНЫЙ анализ через OpenAI
        analysis_result = await openai_service.analyze_moderator_performance(
            messages=messages,
            prompt=prompt,
            moderators=moderators,
            group_name=group_name
        )
        
        # Добавляем метаданные
        analysis_result.update({
            "timestamp": datetime.now().isoformat(),
            "prompt": prompt,
            "analyzed_moderators": moderators,
            "messages_analyzed": len(messages),
            "group_name": group_name
        })
        
        # Сохраняем результаты в базу
        analysis_report = {
            "group_id": group_id,
            "type": "telegram_analysis",
            "results": analysis_result,
            "prompt": prompt,
            "analyzed_moderators": moderators
        }
        
        try:
            supabase_client.table('analysis_reports').insert(analysis_report).execute()
            logger.info("Analysis results saved to database")
        except Exception as db_error:
            logger.warning(f"Failed to save to database: {db_error}")
        
        logger.info(f"OpenAI analysis completed for group {group_id}")
        return {"status": "success", "result": analysis_result}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}")
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


@router.get("/debug/connection")
async def debug_telegram_connection():
    """Диагностика подключения к Telegram API"""
    try:
        logger.info("Starting Telegram connection diagnostics...")
        
        # Проверяем конфигурацию
        config_status = {
            "api_id_configured": bool(settings.TELEGRAM_API_ID),
            "api_hash_configured": bool(settings.TELEGRAM_API_HASH),
            "session_string_configured": bool(settings.TELEGRAM_SESSION_STRING),
            "session_string_length": len(settings.TELEGRAM_SESSION_STRING) if settings.TELEGRAM_SESSION_STRING else 0
        }
        
        # Пробуем подключиться к Telegram
        connection_test = await test_telegram_connection()
        
        return {
            "status": "success",
            "config": config_status,
            "connection": connection_test,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Debug connection failed: {str(e)}")
        return {
            "status": "error",
            "error": str(e),
            "config": config_status if 'config_status' in locals() else {},
            "timestamp": datetime.now().isoformat()
        }

async def test_telegram_connection():
    """Тестирование подключения к Telegram API"""
    try:
        # Получаем информацию о текущем пользователе
        async def get_me_operation():
            me = await telegram_service.client.get_me()
            return {
                "user_id": str(me.id),
                "first_name": me.first_name,
                "last_name": me.last_name,
                "username": me.username,
                "phone": me.phone,
                "is_premium": getattr(me, 'premium', False)
            }
        
        user_info = await telegram_service.execute_telegram_operation(get_me_operation)
        
        # Получаем список диалогов (первые 5)
        async def get_dialogs_operation():
            dialogs = []
            count = 0
            async for dialog in telegram_service.client.iter_dialogs(limit=5):
                dialogs.append({
                    "id": str(dialog.id),
                    "name": dialog.name,
                    "is_group": dialog.is_group,
                    "is_channel": dialog.is_channel,
                    "is_user": dialog.is_user
                })
                count += 1
                if count >= 5:
                    break
            return dialogs
        
        dialogs_info = await telegram_service.execute_telegram_operation(get_dialogs_operation)
        
        return {
            "connected": True,
            "user": user_info,
            "dialogs_count": len(dialogs_info),
            "sample_dialogs": dialogs_info,
            "message": "Successfully connected to Telegram API"
        }
        
    except Exception as e:
        logger.error(f"Telegram connection test failed: {str(e)}")
        return {
            "connected": False,
            "error": str(e),
            "message": "Failed to connect to Telegram API"
        }

@router.get("/debug/group/{group_id}")
async def debug_group_access(group_id: str):
    """Диагностика доступа к конкретной группе"""
    try:
        logger.info(f"Testing access to group {group_id}")
        
        # Проверяем существование группы в БД
        db_group = supabase_client.table('telegram_groups').select("*").eq('id', group_id).execute()
        
        if not db_group.data:
            return {
                "status": "error",
                "error": f"Group {group_id} not found in database"
            }
        
        group_data = db_group.data[0]
        telegram_group_id = group_data["group_id"]
        
        # Тестируем доступ к группе через Telegram API
        async def test_group_access():
            try:
                # Пробуем получить информацию о группе
                entity = await telegram_service.get_entity(telegram_group_id)
                
                # Пробуем получить базовую информацию
                if hasattr(entity, 'title'):
                    title = entity.title
                elif hasattr(entity, 'first_name'):
                    title = f"{entity.first_name} {getattr(entity, 'last_name', '')}"
                else:
                    title = "Unknown"
                
                return {
                    "entity_found": True,
                    "entity_type": type(entity).__name__,
                    "title": title,
                    "telegram_id": str(getattr(entity, 'id', 'unknown'))
                }
            except Exception as e:
                return {
                    "entity_found": False,
                    "error": str(e)
                }
        
        group_access_result = await telegram_service.execute_telegram_operation(test_group_access)
        
        return {
            "status": "success",
            "database_group": {
                "id": group_data["id"],
                "name": group_data["name"],
                "telegram_id": telegram_group_id
            },
            "telegram_access": group_access_result,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Group debug failed: {str(e)}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
    
@router.get("/health")
async def telegram_health_check():
    """Проверка здоровья Telegram API соединения"""
    try:
        health_status = await telegram_service.health_check()
        
        if health_status["status"] == "healthy":
            return health_status
        else:
            raise HTTPException(status_code=503, detail=health_status)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail={
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        })

@router.post("/reconnect")
async def force_telegram_reconnect():
    """Принудительное переподключение к Telegram API"""
    try:
        logger.info("Forcing Telegram reconnection...")
        
        # Отключаемся
        await telegram_service.disconnect()
        
        # Подключаемся заново
        await telegram_service.connect_with_retry(max_retries=3)
        
        # Проверяем статус
        health_status = await telegram_service.health_check()
        
        return {
            "status": "success",
            "message": "Reconnection completed",
            "health": health_status,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Forced reconnection failed: {str(e)}")
        raise HTTPException(status_code=500, detail={
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        })

# Также обновить существующий метод get_group_info
@router.get("/groups/{group_id}/info/detailed")
async def get_detailed_group_info(group_id: str):
    """Получить детальную информацию о группе с диагностикой"""
    try:
        logger.info(f"Getting detailed info for group {group_id}")
        
        # Проверяем группу в БД
        group = supabase_client.table('telegram_groups').select("*").eq('id', group_id).execute()
        
        if not group.data:
            raise HTTPException(status_code=404, detail="Group not found in database")
        
        group_data = group.data[0]
        telegram_group_id = group_data["group_id"]
        
        # Проверяем подключение
        health = await telegram_service.health_check()
        
        if health["status"] != "healthy":
            return {
                "status": "error",
                "message": "Telegram API connection is not healthy",
                "health": health,
                "database_group": group_data
            }
        
        # Получаем актуальную информацию из Telegram
        try:
            telegram_info = await telegram_service.get_group_info(telegram_group_id)
            
            return {
                "status": "success",
                "database_group": group_data,
                "telegram_info": telegram_info,
                "health": health,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as telegram_error:
            logger.error(f"Failed to get Telegram info: {str(telegram_error)}")
            return {
                "status": "partial_success",
                "message": "Database info available, but Telegram API failed",
                "database_group": group_data,
                "telegram_error": str(telegram_error),
                "health": health,
                "timestamp": datetime.now().isoformat()
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Detailed group info failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    

@router.get("/debug/simple/{group_id}")
async def simple_group_debug(group_id: str):
    """Упрощенная диагностика группы без Telegram API вызовов"""
    try:
        logger.info(f"Simple debug for group {group_id}")
        
        # Только проверяем базу данных
        db_group = supabase_client.table('telegram_groups').select("*").eq('id', group_id).execute()
        
        if not db_group.data:
            return {
                "status": "error",
                "error": f"Group {group_id} not found in database"
            }
        
        group_data = db_group.data[0]
        telegram_group_id = group_data["group_id"]
        
        return {
            "status": "success",
            "database_group": group_data,
            "telegram_id": telegram_group_id,
            "ready_for_telegram_test": True,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Simple debug failed: {str(e)}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@router.get("/debug/telegram-entity/{telegram_id}")
async def test_telegram_entity(telegram_id: str):
    """Тестирование получения entity из Telegram"""
    try:
        logger.info(f"Testing Telegram entity for {telegram_id}")
        
        # Простой тест получения entity
        async def get_entity_test():
            try:
                entity = await telegram_service.client.get_entity(int(telegram_id))
                return {
                    "success": True,
                    "entity_type": type(entity).__name__,
                    "entity_id": str(entity.id),
                    "title": getattr(entity, 'title', getattr(entity, 'first_name', 'Unknown'))
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e)
                }
        
        # Выполняем без execute_telegram_operation для простоты
        await telegram_service.ensure_connected()
        result = await get_entity_test()
        
        return {
            "status": "success",
            "telegram_id": telegram_id,
            "entity_test": result,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Entity test failed: {str(e)}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
    
@router.get("/groups/{group_id}/messages/simple")
async def get_group_messages_simple(group_id: str, limit: int = Query(10, ge=1, le=100)):
    """Получить сообщения из группы (упрощенная версия без дополнительных API вызовов)"""
    try:
        logger.debug(f"Fetching simple messages for group {group_id} with limit {limit}")
        
        # Проверяем существование группы
        group = supabase_client.table('telegram_groups').select("*").eq('id', group_id).execute()
        
        if not group.data:
            logger.warning(f"Group with ID {group_id} not found")
            raise HTTPException(status_code=404, detail="Group not found")
        
        # Получаем телеграм ID группы
        telegram_group_id = group.data[0]["group_id"]
        
        # Получаем сообщения через упрощенный метод
        messages_data = await telegram_service.get_messages_simple(telegram_group_id, limit=limit)
        
        logger.debug(f"Successfully fetched {len(messages_data)} simple messages")
        return {
            "status": "success",
            "count": len(messages_data),
            "messages": messages_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching simple messages: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/groups/{group_id}/entity-only")
async def test_entity_only(group_id: str):
    try:
        group = supabase_client.table('telegram_groups').select("*").eq('id', group_id).execute()
        telegram_group_id = group.data[0]["group_id"]
        
        entity = await telegram_service.get_entity(telegram_group_id)
        
        return {
            "status": "success",
            "entity_type": type(entity).__name__,
            "entity_id": str(entity.id),
            "title": getattr(entity, 'title', 'Unknown')
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}
    
@router.get("/groups/{group_id}/test-iter-messages")
async def test_iter_messages_direct(group_id: str):
    """Тест iter_messages без execute_telegram_operation"""
    try:
        group = supabase_client.table('telegram_groups').select("*").eq('id', group_id).execute()
        telegram_group_id = group.data[0]["group_id"]
        
        # Получаем entity
        entity = await telegram_service.get_entity(telegram_group_id)
        
        # Простейший iter_messages без execute_telegram_operation
        messages = []
        count = 0
        async for message in telegram_service.client.iter_messages(entity, limit=1):
            count += 1
            messages.append({"id": str(message.id), "text": message.text or ""})
            break  # Только 1 сообщение
            
        return {"status": "success", "count": count, "messages": messages}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@router.get("/groups/{group_id}/test-iter-timeout")
async def test_iter_messages_with_timeout(group_id: str):
    """Тест iter_messages с таймаутом 15 секунд"""
    try:
        group = supabase_client.table('telegram_groups').select("*").eq('id', group_id).execute()
        telegram_group_id = group.data[0]["group_id"]
        
        # Получаем entity
        entity = await telegram_service.get_entity(telegram_group_id)
        
        # iter_messages с таймаутом
        messages = []
        count = 0
        
        async def get_messages_with_timeout():
            async for message in telegram_service.client.iter_messages(entity, limit=5):
                count += 1
                messages.append({
                    "id": str(message.id), 
                    "text": message.text or "",
                    "date": message.date.isoformat()
                })
                if count >= 5:
                    break
            return messages
        
        # Устанавливаем таймаут 15 секунд
        result = await asyncio.wait_for(get_messages_with_timeout(), timeout=15.0)
        
        return {
            "status": "success", 
            "count": len(result), 
            "messages": result,
            "note": "Completed within timeout"
        }
        
    except asyncio.TimeoutError:
        return {
            "status": "timeout", 
            "error": "iter_messages timed out after 15 seconds",
            "partial_count": count,
            "partial_messages": messages
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}

@router.get("/groups/{group_id}/test-get-messages-alternative")
async def test_get_messages_alternative(group_id: str):
    """Альтернативный метод - get_messages вместо iter_messages"""
    try:
        group = supabase_client.table('telegram_groups').select("*").eq('id', group_id).execute()
        telegram_group_id = group.data[0]["group_id"]
        
        # Получаем entity
        entity = await telegram_service.get_entity(telegram_group_id)
        
        # Пробуем get_messages вместо iter_messages
        messages_result = await telegram_service.client.get_messages(entity, limit=5)
        
        messages = []
        for msg in messages_result:
            if msg:
                messages.append({
                    "id": str(msg.id),
                    "text": msg.text or "",
                    "date": msg.date.isoformat(),
                    "sender_id": str(msg.sender_id) if msg.sender_id else None
                })
        
        return {
            "status": "success",
            "method": "get_messages",
            "count": len(messages),
            "messages": messages
        }
        
    except Exception as e:
        return {"status": "error", "error": str(e)}

@router.get("/groups/{group_id}/test-permissions")
async def test_group_permissions(group_id: str):
    """Проверка прав доступа к группе"""
    try:
        group = supabase_client.table('telegram_groups').select("*").eq('id', group_id).execute()
        telegram_group_id = group.data[0]["group_id"]
        
        # Получаем entity
        entity = await telegram_service.get_entity(telegram_group_id)
        
        # Проверяем тип entity и права
        entity_info = {
            "entity_type": type(entity).__name__,
            "entity_id": str(entity.id),
            "title": getattr(entity, 'title', 'N/A'),
            "username": getattr(entity, 'username', 'N/A'),
        }
        
        # Дополнительная информация для каналов
        if hasattr(entity, 'broadcast'):
            entity_info["is_broadcast"] = entity.broadcast
        if hasattr(entity, 'megagroup'):
            entity_info["is_megagroup"] = entity.megagroup
        if hasattr(entity, 'restricted'):
            entity_info["is_restricted"] = entity.restricted
        if hasattr(entity, 'participants_count'):
            entity_info["participants_count"] = entity.participants_count
            
        # Пробуем получить наши права в группе/канале
        try:
            me = await telegram_service.client.get_me()
            my_participant = await telegram_service.client.get_permissions(entity, me.id)
            
            permissions = {
                "is_admin": my_participant.is_admin if hasattr(my_participant, 'is_admin') else False,
                "can_view_messages": my_participant.view_messages if hasattr(my_participant, 'view_messages') else None,
                "can_send_messages": my_participant.send_messages if hasattr(my_participant, 'send_messages') else None,
                "is_banned": my_participant.is_banned if hasattr(my_participant, 'is_banned') else False,
            }
        except Exception as perm_error:
            permissions = {"error": str(perm_error)}
        
        return {
            "status": "success",
            "entity_info": entity_info,
            "my_permissions": permissions
        }
        
    except Exception as e:
        return {"status": "error", "error": str(e)}

@router.get("/groups/{group_id}/test-combined-approach")
async def test_combined_approach(group_id: str):
    """Комбинированный подход с fallback методами"""
    try:
        group = supabase_client.table('telegram_groups').select("*").eq('id', group_id).execute()
        telegram_group_id = group.data[0]["group_id"]
        
        # Получаем entity
        entity = await telegram_service.get_entity(telegram_group_id)
        
        results = {
            "entity_acquired": True,
            "methods_tested": {}
        }
        
        # Метод 1: iter_messages с коротким таймаутом
        try:
            messages = []
            async def quick_iter():
                count = 0
                async for message in telegram_service.client.iter_messages(entity, limit=2):
                    messages.append({
                        "id": str(message.id),
                        "text": message.text[:50] if message.text else ""
                    })
                    count += 1
                    if count >= 2:
                        break
                return messages
            
            result1 = await asyncio.wait_for(quick_iter(), timeout=5.0)
            results["methods_tested"]["iter_messages"] = {
                "status": "success",
                "count": len(result1),
                "timeout": "5s"
            }
        except asyncio.TimeoutError:
            results["methods_tested"]["iter_messages"] = {
                "status": "timeout",
                "timeout": "5s"
            }
        except Exception as e:
            results["methods_tested"]["iter_messages"] = {
                "status": "error",
                "error": str(e)
            }
        
        # Метод 2: get_messages
        try:
            messages_result = await telegram_service.client.get_messages(entity, limit=2)
            results["methods_tested"]["get_messages"] = {
                "status": "success",
                "count": len([m for m in messages_result if m]),
                "method": "direct_get"
            }
        except Exception as e:
            results["methods_tested"]["get_messages"] = {
                "status": "error",
                "error": str(e)
            }
        
        # Метод 3: get_messages с конкретными ID (если знаем последние)
        try:
            # Получаем последние сообщения по ID
            messages_by_ids = await telegram_service.client.get_messages(entity, ids=None, limit=1)
            if messages_by_ids and len(messages_by_ids) > 0:
                latest_msg = messages_by_ids[0]
                if latest_msg:
                    results["methods_tested"]["get_messages_by_ids"] = {
                        "status": "success",
                        "latest_message_id": str(latest_msg.id),
                        "method": "by_ids"
                    }
                else:
                    results["methods_tested"]["get_messages_by_ids"] = {
                        "status": "empty",
                        "method": "by_ids"
                    }
            else:
                results["methods_tested"]["get_messages_by_ids"] = {
                    "status": "no_messages",
                    "method": "by_ids"
                }
        except Exception as e:
            results["methods_tested"]["get_messages_by_ids"] = {
                "status": "error",
                "error": str(e)
            }
        
        # Определяем рекомендуемый метод
        if results["methods_tested"].get("get_messages", {}).get("status") == "success":
            results["recommended_method"] = "get_messages"
        elif results["methods_tested"].get("iter_messages", {}).get("status") == "success":
            results["recommended_method"] = "iter_messages"
        else:
            results["recommended_method"] = "none_working"
        
        return {
            "status": "success",
            "telegram_group_id": telegram_group_id,
            "results": results
        }
        
    except Exception as e:
        return {"status": "error", "error": str(e)}