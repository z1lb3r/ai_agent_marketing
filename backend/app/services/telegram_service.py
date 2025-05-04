# backend/app/services/telegram_service.py
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.types import Message, User, Channel
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from ..core.config import settings
import logging

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
        offset_date: Optional[datetime] = None
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
                    messages.append({
                        'id': message.id,
                        'text': message.text,
                        'date': message.date.isoformat(),
                        'sender_id': message.sender_id,
                        'reply_to_msg_id': message.reply_to_msg_id
                    })
            
            return messages
        finally:
            await self.disconnect()
    
    async def get_group_info(self, group_id: str) -> Dict[str, Any]:
        """Получить информацию о группе"""
        await self.connect()
        
        try:
            entity = await self.client.get_entity(group_id)
            if isinstance(entity, Channel):
                return {
                    'id': entity.id,
                    'title': entity.title,
                    'username': entity.username,
                    'participants_count': entity.participants_count
                }
            return {}
        finally:
            await self.disconnect()
    
    async def get_moderators(self, group_id: str) -> List[Dict[str, Any]]:
        """Получить список модераторов группы"""
        await self.connect()
        
        try:
            moderators = []
            async for user in self.client.iter_participants(
                group_id, 
                filter='admin'
            ):
                if isinstance(user, User):
                    moderators.append({
                        'id': user.id,
                        'username': user.username,
                        'first_name': user.first_name,
                        'last_name': user.last_name
                    })
            
            return moderators
        finally:
            await self.disconnect()