# backend/app/services/telegram_service.py
from telethon import TelegramClient, types
from telethon.sessions import StringSession
from telethon.tl.types import Message, User, Channel, Chat
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import asyncio
import uuid
import logging
from ..core.config import settings
from ..core.database import supabase_client

logger = logging.getLogger(__name__)

class TelegramService:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self.api_id = settings.TELEGRAM_API_ID
        self.api_hash = settings.TELEGRAM_API_HASH
        self.session_string = settings.TELEGRAM_SESSION_STRING
        
        # Создаем клиента сразу, но не подключаемся
        self.client = TelegramClient(
            StringSession(self.session_string),
            self.api_id,
            self.api_hash
        )
        
        # Замок для синхронизации доступа к клиенту
        self.client_lock = asyncio.Lock()
        
        # Отслеживаем состояние подключения
        self.is_connected = False
        self._initialized = True
        
        logger.info("TelegramService initialized")
    
    async def start(self):
        """Запуск клиента при старте приложения"""
        try:
            if not self.is_connected:
                logger.info("Starting Telegram client...")
                await self.client.start()
                self.is_connected = True
                logger.info("Telegram client started successfully")
        except Exception as e:
            logger.error(f"Failed to start Telegram client: {e}")
            self.is_connected = False
            raise
    
    async def close(self):
        """Корректное закрытие клиента при завершении работы приложения"""
        if self.is_connected:
            logger.info("Disconnecting Telegram client...")
            try:
                # Освобождаем блокировку, если она активна
                if self.client_lock.locked():
                    self.client_lock.release()
                    
                # Отключаем клиента с таймаутом
                await asyncio.wait_for(self.client.disconnect(), timeout=3.0)
                self.is_connected = False
                logger.info("Telegram client disconnected")
            except Exception as e:
                logger.error(f"Error during disconnect: {e}")
                # Принудительно освобождаем ресурсы
                self.client = None
                self.is_connected = False
    
    async def ensure_connected(self):
        """Проверка и восстановление соединения при необходимости"""
        if not self.client.is_connected():
            logger.info("Client is not connected, reconnecting...")
            try:
                await self.client.connect()
                
                # Проверяем авторизацию
                is_authorized = await self.client.is_user_authorized()
                if not is_authorized:
                    logger.warning("User is not authorized. Session might be invalid.")
                    raise ValueError("User is not authorized. Please provide a valid session string.")
                
                self.is_connected = True
                logger.info("Reconnected successfully")
            except Exception as e:
                self.is_connected = False
                logger.error(f"Failed to reconnect: {e}")
                raise
    
    async def execute_telegram_operation(self, operation):
        """
        Выполняет операцию с Telegram API с обработкой соединения и блокировкой.
        
        Этот метод гарантирует, что:
        1. Клиент подключен
        2. Операция выполняется эксклюзивно (без конкурентного доступа)
        3. Операция повторяется при временных проблемах
        """
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                # Используем блокировку для предотвращения конкурентного доступа
                async with self.client_lock:
                    # Проверяем и восстанавливаем соединение
                    await self.ensure_connected()
                    
                    # Выполняем операцию
                    return await operation()
                    
            except asyncio.CancelledError:
                logger.warning(f"Operation was cancelled (attempt {attempt+1}/{max_retries})")
                if attempt == max_retries - 1:
                    logger.error("All retry attempts failed due to cancellation")
                    raise ValueError("Operation was repeatedly cancelled. Please try again later.")
                
                # Экспоненциальная задержка перед повторной попыткой
                await asyncio.sleep(retry_delay * (2 ** attempt))
                
            except Exception as e:
                logger.error(f"Operation failed (attempt {attempt+1}/{max_retries}): {e}")
                if attempt == max_retries - 1:
                    logger.error("All retry attempts failed")
                    raise
                
                # Экспоненциальная задержка перед повторной попыткой
                await asyncio.sleep(retry_delay * (2 ** attempt))
    
    async def get_group_messages(
        self, 
        group_id: str, 
        limit: int = 100,
        offset_date: Optional[datetime] = None,
        include_replies: bool = True,
        get_users: bool = True,
        save_to_db: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Получить сообщения из группы с дополнительной информацией
        
        Args:
            group_id: ID группы
            limit: Максимальное количество сообщений
            offset_date: Дата, с которой начинать получение сообщений
            include_replies: Включать ли ответы на сообщения
            get_users: Получать ли информацию о пользователях
            save_to_db: Сохранять ли сообщения в базу данных
            
        Returns:
            Список сообщений с дополнительной информацией
        """
        async def operation():
            entity = await self.get_entity(group_id)
            
            messages = []
            users_cache = {}  # Кэш пользователей для уменьшения запросов
            
            # Получаем сообщения
            async for message in self.client.iter_messages(
                entity, 
                limit=limit,
                offset_date=offset_date
            ):
                if isinstance(message, Message):
                    # Базовая информация о сообщении
                    msg = {
                        'message_id': str(message.id),
                        'text': message.text or "",
                        'date': message.date.isoformat(),
                        'sender_id': str(message.sender_id) if message.sender_id else None,
                        'is_reply': message.reply_to is not None,
                        'reply_to_message_id': str(message.reply_to.reply_to_msg_id) if message.reply_to else None,
                        'has_media': message.media is not None,
                        'edit_date': message.edit_date.isoformat() if message.edit_date else None,
                        'views': message.views if hasattr(message, 'views') else None,
                        'reactions': []
                    }
                    
                    # Добавляем информацию о реакциях
                    if hasattr(message, 'reactions') and message.reactions:
                        for reaction in message.reactions.results:
                            msg['reactions'].append({
                                'emoji': reaction.reaction,
                                'count': reaction.count
                            })
                    
                    # Получаем информацию об отправителе, если нужно
                    if get_users and message.sender_id:
                        sender_id = str(message.sender_id)
                        if sender_id not in users_cache:
                            try:
                                sender = await message.get_sender()
                                users_cache[sender_id] = {
                                    'id': sender_id,
                                    'username': getattr(sender, 'username', None),
                                    'first_name': getattr(sender, 'first_name', None),
                                    'last_name': getattr(sender, 'last_name', None),
                                    'is_bot': getattr(sender, 'bot', False),
                                    'is_premium': getattr(sender, 'premium', False) if hasattr(sender, 'premium') else False
                                }
                            except Exception as e:
                                logger.warning(f"Failed to get sender for message {message.id}: {e}")
                        
                        if sender_id in users_cache:
                            msg['sender'] = users_cache[sender_id]
                    
                    # Получаем сообщение, на которое отвечают
                    if include_replies and message.reply_to:
                        try:
                            replied_msg = await message.get_reply_message()
                            if replied_msg:
                                msg['replied_message'] = {
                                    'message_id': str(replied_msg.id),
                                    'text': replied_msg.text or "",
                                    'date': replied_msg.date.isoformat(),
                                    'sender_id': str(replied_msg.sender_id) if replied_msg.sender_id else None
                                }
                                
                                # Добавляем информацию об отправителе сообщения, на которое отвечают
                                if get_users and replied_msg.sender_id:
                                    replied_sender_id = str(replied_msg.sender_id)
                                    if replied_sender_id not in users_cache:
                                        try:
                                            replied_sender = await replied_msg.get_sender()
                                            users_cache[replied_sender_id] = {
                                                'id': replied_sender_id,
                                                'username': getattr(replied_sender, 'username', None),
                                                'first_name': getattr(replied_sender, 'first_name', None),
                                                'last_name': getattr(replied_sender, 'last_name', None),
                                                'is_bot': getattr(replied_sender, 'bot', False)
                                            }
                                        except Exception as e:
                                            logger.warning(f"Failed to get sender for replied message {replied_msg.id}: {e}")
                                    
                                    if replied_sender_id in users_cache:
                                        msg['replied_message']['sender'] = users_cache[replied_sender_id]
                        except Exception as e:
                            logger.warning(f"Failed to get replied message for message {message.id}: {e}")
                    
                    messages.append(msg)
                    
                    # Сохраняем в базу данных если требуется
                    if save_to_db:
                        await self._save_message_to_db(group_id, msg)
                        
                        # Сохраняем пользователей
                        if get_users:
                            for user_id, user_data in users_cache.items():
                                is_moderator = await self._check_if_moderator(entity, user_id)
                                user_data['is_moderator'] = is_moderator
                                await self._save_user_to_db(user_data, group_id)
            
            logger.info(f"Retrieved {len(messages)} messages from group {group_id}")
            return messages
        
        try:
            return await self.execute_telegram_operation(operation)
        except Exception as e:
            logger.error(f"Error retrieving messages from group {group_id}: {e}")
            raise
    
    async def _save_message_to_db(self, group_id: str, message: Dict[str, Any]):
        """Сохранить сообщение в базу данных"""
        try:
            # Сначала получаем ID группы из базы
            db_group = supabase_client.table('telegram_groups').select('id').eq('group_id', group_id).execute()
            
            if not db_group.data:
                logger.warning(f"Group with telegram_id {group_id} not found in database")
                return
                
            db_group_id = db_group.data[0]['id']
            
            # Проверяем, есть ли уже такое сообщение в базе
            existing_msg = supabase_client.table('telegram_messages').select('id')\
                .eq('group_id', db_group_id)\
                .eq('message_id', message['message_id']).execute()
            
            if not existing_msg.data:
                # Создаем запись в базе
                msg_for_db = {
                    'group_id': db_group_id,
                    'message_id': message['message_id'],
                    'sender_id': message['sender_id'],
                    'text': message['text'],
                    'date': message['date'],
                    'is_reply': message['is_reply'],
                    'reply_to_message_id': message['reply_to_message_id']
                }
                supabase_client.table('telegram_messages').insert(msg_for_db).execute()
                logger.debug(f"Message {message['message_id']} saved to database")
        except Exception as e:
            logger.error(f"Error saving message to database: {e}")
    
    async def get_group_info(self, group_id: str) -> Dict[str, Any]:
        """Получить информацию о группе"""
        async def operation():
            entity = await self.client.get_entity(group_id)
            group_info = {}
            
            if isinstance(entity, Channel) or isinstance(entity, Chat):
                # Получаем базовую информацию о группе
                group_info = {
                    'id': str(entity.id),
                    'title': getattr(entity, 'title', 'Unknown'),
                    'username': getattr(entity, 'username', None),
                    'description': getattr(entity, 'about', None) if hasattr(entity, 'about') else None,
                    'participants_count': getattr(entity, 'participants_count', None) if hasattr(entity, 'participants_count') else None,
                    'date': getattr(entity, 'date', datetime.now()).isoformat() if hasattr(entity, 'date') else datetime.now().isoformat(),
                    'is_public': bool(getattr(entity, 'username', None))
                }
                
                # Дополнительная информация для каналов
                if isinstance(entity, Channel):
                    group_info.update({
                        'is_broadcast': getattr(entity, 'broadcast', False),
                        'is_megagroup': getattr(entity, 'megagroup', False)
                    })
                
                # Сохраняем или обновляем информацию в базе данных
                await self._save_group_to_db(group_info)
                
                logger.info(f"Retrieved info for group {group_id}")
                return group_info
            
            logger.warning(f"Entity {group_id} is not a group or channel")
            return {}
            
        try:
            return await self.execute_telegram_operation(operation)
        except Exception as e:
            logger.error(f"Error retrieving group info for {group_id}: {e}")
            raise
    
    async def _save_group_to_db(self, group_info: Dict[str, Any]):
        """Сохранить или обновить информацию о группе в базе данных"""
        try:
            # Проверяем, есть ли группа в базе
            existing_group = supabase_client.table('telegram_groups').select('id').eq('group_id', group_info['id']).execute()
            
            # Подготовка данных для базы
            group_data = {
                'name': group_info['title'],
                'settings': {
                    'members_count': group_info.get('participants_count'),
                    'username': group_info.get('username'),
                    'description': group_info.get('description'),
                    'is_public': group_info.get('is_public', False),
                    'is_broadcast': group_info.get('is_broadcast', False),
                    'is_megagroup': group_info.get('is_megagroup', False)
                }
            }
            
            if existing_group.data:
                # Обновляем существующую группу
                supabase_client.table('telegram_groups').update(group_data).eq('group_id', group_info['id']).execute()
                logger.debug(f"Updated group {group_info['id']} in database")
            else:
                # Создаем новую группу
                group_data['group_id'] = group_info['id']
                supabase_client.table('telegram_groups').insert(group_data).execute()
                logger.debug(f"Added new group {group_info['id']} to database")
        except Exception as e:
            logger.error(f"Error saving group to database: {e}")
    
    async def get_moderators(self, group_id: str, save_to_db: bool = False) -> List[Dict[str, Any]]:
        """Получить список модераторов группы"""
        async def operation():
            entity = await self.get_entity(group_id)
            
            moderators = []
            async for user in self.client.iter_participants(
                entity, 
                filter='admin'
            ):
                if isinstance(user, User):
                    mod = {
                        'telegram_id': str(user.id),
                        'username': user.username,
                        'first_name': user.first_name,
                        'last_name': user.last_name,
                        'is_bot': user.bot,
                        'is_moderator': True,
                        'photo_url': None
                    }
                    moderators.append(mod)
                    
                    # Сохраняем в базу данных если требуется
                    if save_to_db:
                        await self._save_user_to_db(mod, group_id)
            
            logger.info(f"Retrieved {len(moderators)} moderators from group {group_id}")
            return moderators
            
        try:
            return await self.execute_telegram_operation(operation)
        except Exception as e:
            logger.error(f"Error retrieving moderators from group {group_id}: {e}")
            raise
    
    async def _save_user_to_db(self, user_data: Dict[str, Any], group_id: str = None):
        """Сохранить или обновить информацию о пользователе в базе данных"""
        try:
            # Проверяем, есть ли уже такой пользователь в базе
            existing_user = supabase_client.table('telegram_users').select('id')\
                .eq('telegram_id', user_data['telegram_id']).execute()
            
            if not existing_user.data:
                # Создаем запись в базе
                supabase_client.table('telegram_users').insert(user_data).execute()
                logger.debug(f"Added new user {user_data['telegram_id']} to database")
            else:
                # Обновляем существующую запись
                user_id = existing_user.data[0]['id']
                supabase_client.table('telegram_users').update({
                    'username': user_data['username'],
                    'first_name': user_data['first_name'],
                    'last_name': user_data['last_name'],
                    'is_bot': user_data.get('is_bot', False),
                    'is_moderator': user_data['is_moderator'],
                    'photo_url': user_data.get('photo_url')
                }).eq('id', user_id).execute()
                logger.debug(f"Updated user {user_data['telegram_id']} in database")
            
            # Если указан group_id, добавляем связь пользователя с группой
            if group_id:
                db_group = supabase_client.table('telegram_groups').select('id').eq('group_id', group_id).execute()
                if db_group.data:
                    db_group_id = db_group.data[0]['id']
                    db_user = supabase_client.table('telegram_users').select('id').eq('telegram_id', user_data['telegram_id']).execute()
                    
                    if db_user.data:
                        db_user_id = db_user.data[0]['id']
                        
                        # Проверяем, существует ли уже связь
                        existing_relation = supabase_client.table('user_group_relations').select('id')\
                            .eq('user_id', db_user_id)\
                            .eq('group_id', db_group_id).execute()
                        
                        if not existing_relation.data:
                            # Создаем связь
                            relation_data = {
                                'user_id': db_user_id,
                                'group_id': db_group_id,
                                'role': 'moderator' if user_data['is_moderator'] else 'user'
                            }
                            supabase_client.table('user_group_relations').insert(relation_data).execute()
                            logger.debug(f"Added user-group relation for user {user_data['telegram_id']} and group {group_id}")
        except Exception as e:
            logger.error(f"Error saving user to database: {e}")
    
    async def collect_group_data(self, group_id: str, messages_limit: int = 100) -> Dict[str, Any]:
        """Собрать все данные о группе и сохранить в базу"""
        try:
            # Получаем информацию о группе
            group_info = await self.get_group_info(group_id)
            
            # Получаем модераторов
            moderators = await self.get_moderators(group_id, save_to_db=True)
            
            # Получаем сообщения
            messages = await self.get_group_messages(group_id, limit=messages_limit, save_to_db=True)
            
            logger.info(f"Collected data for group {group_id}: {len(messages)} messages, {len(moderators)} moderators")
            
            return {
                'group': group_info,
                'moderators': moderators,
                'messages': messages
            }
        except Exception as e:
            logger.error(f"Error collecting data for group {group_id}: {e}")
            raise
    
    async def get_group_members(self, group_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Получить участников группы"""
        async def operation():
            entity = await self.get_entity(group_id)
            
            members = []
            async for user in self.client.iter_participants(entity, limit=limit):
                if isinstance(user, User):
                    member = {
                        'telegram_id': str(user.id),
                        'username': user.username,
                        'first_name': user.first_name,
                        'last_name': user.last_name,
                        'is_bot': user.bot,
                        'is_moderator': False,  # По умолчанию не модератор
                        'date_joined': None  # Telegram API не предоставляет эту информацию напрямую
                    }
                    members.append(member)
            
            logger.info(f"Retrieved {len(members)} members from group {group_id}")
            return members
            
        try:
            return await self.execute_telegram_operation(operation)
        except Exception as e:
            logger.error(f"Error retrieving members from group {group_id}: {e}")
            raise
    
    async def get_message_reactions(self, group_id: str, message_id: int) -> List[Dict[str, Any]]:
        """Получить реакции на сообщение"""
        async def operation():
            entity = await self.get_entity(group_id)
            
            # Получаем сообщение
            message = await self.client.get_messages(entity, ids=message_id)
            
            if not message or not hasattr(message, 'reactions'):
                return []
                
            reactions = []
            if message.reactions:
                for reaction in message.reactions.results:
                    reactions.append({
                        'emoji': reaction.reaction,
                        'count': reaction.count
                    })
            
            return reactions
            
        try:
            return await self.execute_telegram_operation(operation)
        except Exception as e:
            logger.error(f"Error retrieving reactions for message {message_id} in group {group_id}: {e}")
            return []
    
    async def get_message_thread(self, group_id: str, message_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """Получить ветку сообщений (ответы на конкретное сообщение)"""
        async def operation():
            entity = await self.get_entity(group_id)
            
            # Получаем сообщение
            thread_messages = []
            async for message in self.client.iter_messages(
                entity, 
                reply_to=message_id,
                limit=limit
            ):
                if isinstance(message, Message):
                    msg = {
                        'message_id': str(message.id),
                        'text': message.text or "",
                        'date': message.date.isoformat(),
                        'sender_id': str(message.sender_id) if message.sender_id else None,
                        'is_reply': True,
                        'reply_to_message_id': str(message_id)
                    }
                    thread_messages.append(msg)
            
            return thread_messages
            
        try:
            return await self.execute_telegram_operation(operation)
        except Exception as e:
            logger.error(f"Error retrieving thread for message {message_id} in group {group_id}: {e}")
            return []

    async def get_entity(self, entity_id: str):
        """Получить сущность Telegram по ID или имени"""
        async def operation():
            # Проверяем, является ли entity_id числом (ID группы/канала)
            if str(entity_id).lstrip('-').isdigit():
                # Если это число, преобразуем его в PeerChannel или PeerChat
                if str(entity_id).startswith('-100'):
                    # Это ID канала в формате -100xxxxxxxxx
                    channel_id = int(str(entity_id)[4:])
                    return types.InputPeerChannel(channel_id=channel_id, access_hash=0)
                elif str(entity_id).startswith('-'):
                    # Это ID группы в формате -xxxxxxxxx
                    chat_id = abs(int(entity_id))
                    return types.InputPeerChat(chat_id=chat_id)
                else:
                    # Это ID пользователя
                    user_id = int(entity_id)
                    return types.InputPeerUser(user_id=user_id, access_hash=0)
            
            # Если это не число, пытаемся получить сущность как обычно
            return await self.client.get_entity(entity_id)
            
        try:
            return await self.execute_telegram_operation(operation)
        except Exception as e:
            logger.error(f"Error getting entity {entity_id}: {e}")
            raise
            
    async def generate_session_string(self, phone: str):
        """
        Генерация строки сессии для последующего использования
        Требует интерактивного ввода кода подтверждения
        """
        client = TelegramClient(
            StringSession(), 
            self.api_id,
            self.api_hash
        )
        
        try:
            await client.connect()
            await client.send_code_request(phone)
            
            # В реальном приложении здесь должен быть механизм получения кода от пользователя
            # Например, через веб-интерфейс или API endpoint
            code = input("Enter the code you received: ")
            await client.sign_in(phone, code)
            
            session_string = client.session.save()
            logger.info("Session string generated successfully")
            
            return session_string
        except Exception as e:
            logger.error(f"Error generating session string: {e}")
            raise
        finally:
            if client.is_connected():
                await client.disconnect()

    async def get_group_info_by_link(self, link_or_username: str) -> Dict[str, Any]:
        """Получить информацию о группе по ссылке или username"""
        async def operation():
            try:
                entity = await self.client.get_entity(link_or_username)
                
                group_info = {}
                
                if isinstance(entity, Channel) or isinstance(entity, Chat):
                    # Получаем базовую информацию о группе
                    group_info = {
                        'id': str(entity.id),
                        'title': getattr(entity, 'title', 'Unknown'),
                        'username': getattr(entity, 'username', None),
                        'description': getattr(entity, 'about', None) if hasattr(entity, 'about') else None,
                        'participants_count': getattr(entity, 'participants_count', None) if hasattr(entity, 'participants_count') else None,
                        'date': getattr(entity, 'date', datetime.now()).isoformat() if hasattr(entity, 'date') else datetime.now().isoformat(),
                        'is_public': bool(getattr(entity, 'username', None))
                    }
                    
                    # Дополнительная информация для каналов
                    if isinstance(entity, Channel):
                        group_info.update({
                            'is_broadcast': getattr(entity, 'broadcast', False),
                            'is_megagroup': getattr(entity, 'megagroup', False)
                        })
                    
                    logger.info(f"Retrieved info for group {link_or_username}")
                    return group_info
                
                logger.warning(f"Entity {link_or_username} is not a group or channel")
                return {}
            except Exception as e:
                logger.error(f"Error getting entity {link_or_username}: {e}")
                return {}
                
        try:
            return await self.execute_telegram_operation(operation)
        except Exception as e:
            logger.error(f"Error retrieving group info for {link_or_username}: {e}")
            return {}
        
    async def _check_if_moderator(self, entity, user_id: str) -> bool:
        """Проверить, является ли пользователь модератором группы"""
        try:
            # Преобразуем user_id из строки в int
            user_id_int = int(user_id)
            
            # Получаем информацию о правах пользователя
            participant = await self.client.get_permissions(entity, user_id_int)
            
            # Проверяем права администратора
            return participant.is_admin
        except Exception as e:
            logger.warning(f"Failed to check if user {user_id} is moderator: {e}")
            return False
        
    async def get_conversation_threads(self, group_id: str, days_back: int = 7) -> List[Dict[str, Any]]:
        """
        Получить цепочки диалогов между пользователями и модераторами
        
        Args:
            group_id: ID группы
            days_back: За сколько дней назад получать сообщения
            
        Returns:
            Список цепочек диалогов
        """
        try:
            # Вычисляем дату, с которой начинать получение сообщений
            offset_date = datetime.now() - timedelta(days=days_back)
            
            # Получаем сообщения
            messages = await self.get_group_messages(
                group_id, 
                limit=500,  # Увеличиваем лимит для более полного анализа
                offset_date=offset_date,
                include_replies=True,
                get_users=True
            )
            
            # Организуем сообщения по цепочкам
            threads = {}
            standalone_messages = []
            
            # Сначала группируем сообщения по reply_to_message_id
            for msg in messages:
                if msg['is_reply'] and msg['reply_to_message_id']:
                    thread_id = msg['reply_to_message_id']
                    if thread_id not in threads:
                        threads[thread_id] = {
                            'root_message_id': thread_id,
                            'messages': []
                        }
                    threads[thread_id]['messages'].append(msg)
                else:
                    standalone_messages.append(msg)
            
            # Дополняем цепочки корневыми сообщениями
            for msg in standalone_messages:
                if msg['message_id'] in threads:
                    threads[msg['message_id']]['root_message'] = msg
            
            # Преобразуем в список и сортируем по дате
            thread_list = []
            for thread_id, thread in threads.items():
                if 'root_message' in thread:
                    # Добавляем дополнительную информацию о цепочке
                    thread['start_date'] = thread['root_message']['date']
                    thread['participants'] = set()
                    thread['moderator_involved'] = False
                    
                    # Добавляем отправителя корневого сообщения
                    if 'sender' in thread['root_message']:
                        thread['participants'].add(thread['root_message']['sender']['id'])
                        if thread['root_message']['sender'].get('is_moderator', False):
                            thread['moderator_involved'] = True
                    
                    # Добавляем отправителей ответов
                    for msg in thread['messages']:
                        if 'sender' in msg:
                            thread['participants'].add(msg['sender']['id'])
                            if msg['sender'].get('is_moderator', False):
                                thread['moderator_involved'] = True
                    
                    # Конвертируем set в list для сериализации
                    thread['participants'] = list(thread['participants'])
                    
                    # Вычисляем время первого ответа модератора
                    if thread['moderator_involved']:
                        thread['first_moderator_response_time'] = self._calculate_first_response_time(
                            thread['root_message'],
                            thread['messages']
                        )
                    
                    thread_list.append(thread)
            
            # Сортируем по дате начала, самые новые первыми
            thread_list.sort(key=lambda x: x['start_date'], reverse=True)
            
            return thread_list
        except Exception as e:
            logger.error(f"Error getting conversation threads for group {group_id}: {e}")
            raise

    def _calculate_first_response_time(self, root_message: Dict[str, Any], replies: List[Dict[str, Any]]) -> Optional[float]:
        """
        Вычислить время первого ответа модератора на сообщение
        
        Args:
            root_message: Корневое сообщение
            replies: Ответы на сообщение
            
        Returns:
            Время ответа в минутах или None, если ответа не было
        """
        # Проверяем, что корневое сообщение не от модератора
        if root_message.get('sender', {}).get('is_moderator', False):
            return None
        
        # Сортируем ответы по дате
        sorted_replies = sorted(replies, key=lambda x: x['date'])
        
        # Ищем первый ответ от модератора
        for reply in sorted_replies:
            if reply.get('sender', {}).get('is_moderator', False):
                # Преобразуем строки в datetime
                root_date = datetime.fromisoformat(root_message['date'].replace('Z', '+00:00'))
                reply_date = datetime.fromisoformat(reply['date'].replace('Z', '+00:00'))
                
                # Вычисляем разницу в минутах
                time_diff = (reply_date - root_date).total_seconds() / 60
                return time_diff
        
        return None
    
    async def prepare_data_for_analysis(self, group_id: str, days_back: int = 7) -> Dict[str, Any]:
        """
        Подготовить данные для анализа
        
        Args:
            group_id: ID группы
            days_back: За сколько дней назад получать данные
            
        Returns:
            Словарь с данными для анализа
        """
        try:
            # Получаем информацию о группе
            group_info = await self.get_group_info(group_id)
            
            # Получаем модераторов
            moderators = await self.get_moderators(group_id, save_to_db=True)
            
            # Получаем цепочки диалогов
            threads = await self.get_conversation_threads(group_id, days_back)
            
            # Вычисляем метрики
            metrics = self._calculate_metrics(threads, moderators)
            
            # Формируем данные для анализа
            analysis_data = {
                'group': group_info,
                'period': {
                    'start_date': (datetime.now() - timedelta(days=days_back)).isoformat(),
                    'end_date': datetime.now().isoformat(),
                    'days': days_back
                },
                'moderators': moderators,
                'conversation_threads': threads,
                'metrics': metrics
            }
            
            return analysis_data
        except Exception as e:
            logger.error(f"Error preparing data for analysis for group {group_id}: {e}")
            raise

    def _calculate_metrics(self, threads: List[Dict[str, Any]], moderators: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Вычислить метрики на основе данных о диалогах
        
        Args:
            threads: Цепочки диалогов
            moderators: Модераторы группы
            
        Returns:
            Словарь с метриками
        """
        # Инициализируем метрики
        metrics = {
            'total_threads': len(threads),
            'moderator_involved_threads': 0,
            'response_times': [],
            'response_time_avg': None,
            'response_time_min': None,
            'response_time_max': None,
            'moderator_activity': {},
            'thread_length_avg': 0
        }
        
        # Инициализируем данные по модераторам
        for mod in moderators:
            mod_id = mod['telegram_id']
            metrics['moderator_activity'][mod_id] = {
                'threads_participated': 0,
                'messages_sent': 0,
                'avg_response_time': None,
                'response_times': []
            }
        
        # Обрабатываем каждую цепочку
        total_messages = 0
        for thread in threads:
            # Считаем общее количество сообщений
            thread_messages = len(thread.get('messages', [])) + 1  # +1 для корневого сообщения
            total_messages += thread_messages
            
            # Если в цепочке участвовал модератор
            if thread.get('moderator_involved', False):
                metrics['moderator_involved_threads'] += 1
                
                # Добавляем время ответа, если есть
                response_time = thread.get('first_moderator_response_time')
                if response_time is not None:
                    metrics['response_times'].append(response_time)
                    
                    # Обновляем статистику по каждому модератору
                    for msg in thread.get('messages', []):
                        if msg.get('sender', {}).get('is_moderator', False):
                            mod_id = msg['sender']['id']
                            if mod_id in metrics['moderator_activity']:
                                metrics['moderator_activity'][mod_id]['threads_participated'] += 1
                                metrics['moderator_activity'][mod_id]['messages_sent'] += 1
                                
                                # Вычисляем время ответа для конкретного модератора
                                if 'replied_message' in msg:
                                    root_date = datetime.fromisoformat(msg['replied_message']['date'].replace('Z', '+00:00'))
                                    msg_date = datetime.fromisoformat(msg['date'].replace('Z', '+00:00'))
                                    mod_response_time = (msg_date - root_date).total_seconds() / 60
                                    metrics['moderator_activity'][mod_id]['response_times'].append(mod_response_time)
        
        # Вычисляем среднюю длину цепочки
        if metrics['total_threads'] > 0:
            metrics['thread_length_avg'] = total_messages / metrics['total_threads']
        
        # Вычисляем статистику по времени ответа
        if metrics['response_times']:
            metrics['response_time_avg'] = sum(metrics['response_times']) / len(metrics['response_times'])
            metrics['response_time_min'] = min(metrics['response_times'])
            metrics['response_time_max'] = max(metrics['response_times'])
        
        # Вычисляем среднее время ответа для каждого модератора
        for mod_id, activity in metrics['moderator_activity'].items():
            if activity['response_times']:
                activity['avg_response_time'] = sum(activity['response_times']) / len(activity['response_times'])
        
        return metrics