# backend/app/services/telegram_service.py
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.types import Message, User, Channel
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from ..core.config import settings
from ..core.database import supabase_client
import logging
import uuid

logger = logging.getLogger(__name__)

class TelegramService:
    def __init__(self):
        self.client = TelegramClient(
            StringSession(settings.TELEGRAM_SESSION_STRING),
            settings.TELEGRAM_API_ID,
            settings.TELEGRAM_API_HASH
        )
    
    async def connect(self):
        """Подключение к Telegram"""
        await self.client.start()
        logger.info("Connected to Telegram")
    
    async def disconnect(self):
        """Отключение от Telegram"""
        await self.client.disconnect()
    
    async def get_group_messages(
        self, 
        group_id: str, 
        limit: int = 100,
        offset_date: Optional[datetime] = None,
        save_to_db: bool = False
    ) -> List[Dict[str, Any]]:
        """Получить сообщения из группы"""
        await self.connect()
        
        try:
            messages = []
            async for message in self.client.iter_messages(
                group_id, 
                limit=limit,
                offset_date=offset_date
            ):
                if isinstance(message, Message):
                    msg = {
                        'message_id': str(message.id),
                        'text': message.text,
                        'date': message.date.isoformat(),
                        'sender_id': str(message.sender_id),
                        'is_reply': message.reply_to is not None,
                        'reply_to_message_id': str(message.reply_to.reply_to_msg_id) if message.reply_to else None
                    }
                    messages.append(msg)
                    
                    # Сохраняем в базу данных если требуется
                    if save_to_db:
                        try:
                            # Сначала получаем ID группы из базы
                            db_group = supabase_client.table('telegram_groups').select('id').eq('group_id', group_id).execute()
                            if db_group.data:
                                db_group_id = db_group.data[0]['id']
                                
                                # Проверяем, есть ли уже такое сообщение в базе
                                existing_msg = supabase_client.table('telegram_messages').select('id')\
                                    .eq('group_id', db_group_id)\
                                    .eq('message_id', msg['message_id']).execute()
                                
                                if not existing_msg.data:
                                    # Создаем запись в базе
                                    msg_for_db = {
                                        'group_id': db_group_id,
                                        'message_id': msg['message_id'],
                                        'sender_id': msg['sender_id'],
                                        'text': msg['text'],
                                        'date': msg['date'],
                                        'is_reply': msg['is_reply'],
                                        'reply_to_message_id': msg['reply_to_message_id']
                                    }
                                    supabase_client.table('telegram_messages').insert(msg_for_db).execute()
                        except Exception as e:
                            logger.error(f"Error saving message to DB: {e}")
            
            return messages
        finally:
            await self.disconnect()
    
    async def get_group_info(self, group_id: str) -> Dict[str, Any]:
        """Получить информацию о группе"""
        await self.connect()
        
        try:
            entity = await self.client.get_entity(group_id)
            if isinstance(entity, Channel):
                group_info = {
                    'id': entity.id,
                    'title': entity.title,
                    'username': entity.username,
                    'participants_count': entity.participants_count if hasattr(entity, 'participants_count') else None
                }
                
                # Обновляем информацию в базе данных
                try:
                    # Проверяем, есть ли группа в базе
                    existing_group = supabase_client.table('telegram_groups').select('id').eq('group_id', str(group_info['id'])).execute()
                    
                    if existing_group.data:
                        # Обновляем существующую группу
                        supabase_client.table('telegram_groups').update({
                            'name': group_info['title'],
                            'settings': {
                                'members_count': group_info['participants_count'],
                                'username': group_info['username']
                            }
                        }).eq('group_id', str(group_info['id'])).execute()
                    else:
                        # Создаем новую группу
                        supabase_client.table('telegram_groups').insert({
                            'group_id': str(group_info['id']),
                            'name': group_info['title'],
                            'settings': {
                                'members_count': group_info['participants_count'],
                                'username': group_info['username']
                            }
                        }).execute()
                except Exception as e:
                    logger.error(f"Error updating group in DB: {e}")
                
                return group_info
            return {}
        finally:
            await self.disconnect()
    
    async def get_moderators(self, group_id: str, save_to_db: bool = False) -> List[Dict[str, Any]]:
        """Получить список модераторов группы"""
        await self.connect()
        
        try:
            moderators = []
            async for user in self.client.iter_participants(
                group_id, 
                filter='admin'
            ):
                if isinstance(user, User):
                    mod = {
                        'telegram_id': str(user.id),
                        'username': user.username,
                        'first_name': user.first_name,
                        'last_name': user.last_name,
                        'is_moderator': True
                    }
                    moderators.append(mod)
                    
                    # Сохраняем в базу данных если требуется
                    if save_to_db:
                        try:
                            # Проверяем, есть ли уже такой пользователь в базе
                            existing_user = supabase_client.table('telegram_users').select('id')\
                                .eq('telegram_id', mod['telegram_id']).execute()
                            
                            if not existing_user.data:
                                # Создаем запись в базе
                                supabase_client.table('telegram_users').insert(mod).execute()
                            else:
                                # Обновляем существующую запись
                                supabase_client.table('telegram_users').update({
                                    'username': mod['username'],
                                    'first_name': mod['first_name'],
                                    'last_name': mod['last_name'],
                                    'is_moderator': True
                                }).eq('telegram_id', mod['telegram_id']).execute()
                        except Exception as e:
                            logger.error(f"Error saving user to DB: {e}")
            
            return moderators
        finally:
            await self.disconnect()
    
    async def collect_group_data(self, group_id: str, messages_limit: int = 100) -> Dict[str, Any]:
        """Собрать все данные о группе и сохранить в базу"""
        # Получаем информацию о группе
        group_info = await self.get_group_info(group_id)
        
        # Получаем модераторов
        moderators = await self.get_moderators(group_id, save_to_db=True)
        
        # Получаем сообщения
        messages = await self.get_group_messages(group_id, limit=messages_limit, save_to_db=True)
        
        return {
            'group': group_info,
            'moderators': moderators,
            'messages': messages
        }