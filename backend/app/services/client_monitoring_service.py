# backend/app/services/client_monitoring_service.py
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import re

from ..core.database import supabase_client
from .telegram_service import TelegramService
from .openai_service import OpenAIService

logger = logging.getLogger(__name__)

class ClientMonitoringService:
    def __init__(self):
        self.telegram_service = TelegramService()
        self.openai_service = OpenAIService()
        self.active_monitoring = {}  # Словарь активных мониторингов по user_id
        
    async def start_monitoring(self, user_id: int):
        """Запустить мониторинг для пользователя"""
        try:
            logger.info(f"Starting monitoring for user {user_id}")
            self.active_monitoring[user_id] = True
            
            # Запускаем фоновую задачу мониторинга
            asyncio.create_task(self._monitoring_loop(user_id))
            
        except Exception as e:
            logger.error(f"Error starting monitoring for user {user_id}: {e}")
            raise
    
    async def stop_monitoring(self, user_id: int):
        """Остановить мониторинг для пользователя"""
        try:
            logger.info(f"Stopping monitoring for user {user_id}")
            self.active_monitoring[user_id] = False
            
        except Exception as e:
            logger.error(f"Error stopping monitoring for user {user_id}: {e}")
            raise
    
    async def _monitoring_loop(self, user_id: int):
        """Основной цикл мониторинга для пользователя"""
        while self.active_monitoring.get(user_id, False):
            try:
                # Получаем настройки пользователя
                settings = await self._get_user_settings(user_id)
                
                if not settings or not settings.get('is_active', False):
                    await asyncio.sleep(60)  # Ждем минуту если мониторинг выключен
                    continue
                
                # Проверяем рабочие часы
                if not self._is_active_hours(settings):
                    await asyncio.sleep(300)  # Ждем 5 минут если не рабочие часы
                    continue
                
                # Выполняем поиск и анализ
                await self._search_and_analyze(user_id, settings)
                
                # Ждем следующий цикл
                interval = settings.get('check_interval_minutes', 5) * 60
                await asyncio.sleep(interval)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop for user {user_id}: {e}")
                await asyncio.sleep(60)  # Ждем минуту при ошибке
    
    async def _get_user_settings(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Получить настройки мониторинга пользователя"""
        try:
            supabase = get_supabase()
            result = supabase.table('monitoring_settings').select('*').eq('user_id', user_id).execute()
            
            if result.data:
                return result.data[0]
            return None
            
        except Exception as e:
            logger.error(f"Error getting user settings for {user_id}: {e}")
            return None
    
    def _is_active_hours(self, settings: Dict[str, Any]) -> bool:
        """Проверить, находимся ли мы в рабочих часах"""
        try:
            now = datetime.now().time()
            start_time = datetime.strptime(settings.get('active_hours_start', '09:00'), '%H:%M').time()
            end_time = datetime.strptime(settings.get('active_hours_end', '21:00'), '%H:%M').time()
            
            return start_time <= now <= end_time
            
        except Exception as e:
            logger.error(f"Error checking active hours: {e}")
            return True  # По умолчанию работаем всегда
    
    async def _search_and_analyze(self, user_id: int, settings: Dict[str, Any]):
        """Поиск ключевых слов и анализ найденных сообщений"""
        try:
            logger.info(f"Starting search and analyze for user {user_id}")
            
            # Получаем шаблоны продуктов
            templates = await self._get_user_templates(user_id)
            if not templates:
                logger.info(f"No product templates found for user {user_id}")
                return
            
            # Получаем чаты для мониторинга
            monitored_chats = settings.get('monitored_chats', [])
            if not monitored_chats:
                logger.info(f"No monitored chats configured for user {user_id}")
                return
            
            # Ищем сообщения в каждом чате
            found_messages = await self._search_keywords_in_chats(
                monitored_chats, 
                templates, 
                settings.get('lookback_minutes', 5)
            )
            
            if not found_messages:
                logger.info(f"No messages with keywords found for user {user_id}")
                return
            
            logger.info(f"Found {len(found_messages)} messages with keywords for user {user_id}")
            
            # Анализируем каждое найденное сообщение через ИИ
            for message_data in found_messages:
                await self._analyze_message_with_ai(user_id, message_data, settings)
                
        except Exception as e:
            logger.error(f"Error in search and analyze for user {user_id}: {e}")
    
    async def _get_user_templates(self, user_id: int) -> List[Dict[str, Any]]:
        """Получить активные шаблоны продуктов пользователя"""
        try:
            supabase = get_supabase()
            result = supabase.table('product_templates').select('*').eq('user_id', user_id).eq('is_active', True).execute()
            
            return result.data or []
            
        except Exception as e:
            logger.error(f"Error getting user templates for {user_id}: {e}")
            return []
    
    async def _search_keywords_in_chats(
        self, 
        chat_ids: List[str], 
        templates: List[Dict[str, Any]], 
        lookback_minutes: int
    ) -> List[Dict[str, Any]]:
        """Поиск ключевых слов в сообщениях чатов"""
        found_messages = []
        
        for chat_id in chat_ids:
            try:
                # Получаем свежие сообщения из чата
                recent_messages = await self._get_recent_messages(chat_id, lookback_minutes)
                
                if not recent_messages:
                    continue
                
                # Проверяем каждое сообщение на ключевые слова
                for message in recent_messages:
                    for template in templates:
                        matched_keywords = self._find_keywords_in_text(
                            message.get('text', ''), 
                            template['keywords']
                        )
                        
                        if matched_keywords:
                            found_messages.append({
                                'message': message,
                                'template': template,
                                'chat_id': chat_id,
                                'matched_keywords': matched_keywords
                            })
                            
                            # Прерываем поиск по шаблонам для этого сообщения
                            break
                            
            except Exception as e:
                logger.error(f"Error searching in chat {chat_id}: {e}")
                continue
        
        return found_messages
    
    async def _get_recent_messages(self, chat_id: str, lookback_minutes: int) -> List[Dict[str, Any]]:
        """Получить недавние сообщения из чата"""
        try:
            # Используем существующий метод telegram_service
            # Конвертируем минуты в дни для совместимости
            lookback_days = max(1, lookback_minutes / (60 * 24))
            
            messages = await self.telegram_service.get_group_messages(
                group_id=chat_id,
                limit=100,  # Ограничиваем количество для скорости
                days_back=lookback_days,
                get_users=True
            )
            
            # Фильтруем сообщения по времени
            cutoff_time = datetime.now() - timedelta(minutes=lookback_minutes)
            
            recent_messages = []
            for msg in messages:
                try:
                    msg_time = datetime.fromisoformat(msg['date'].replace('Z', '+00:00'))
                    if msg_time >= cutoff_time:
                        recent_messages.append(msg)
                except:
                    continue
            
            return recent_messages
            
        except Exception as e:
            logger.error(f"Error getting recent messages from {chat_id}: {e}")
            return []
    
    def _find_keywords_in_text(self, text: str, keywords: List[str]) -> List[str]:
        """Найти ключевые слова в тексте"""
        if not text:
            return []
        
        text_lower = text.lower()
        matched_keywords = []
        
        for keyword in keywords:
            keyword_lower = keyword.lower().strip()
            
            # Простой поиск подстроки
            if keyword_lower in text_lower:
                matched_keywords.append(keyword)
        
        return matched_keywords
    
    async def _analyze_message_with_ai(
        self, 
        user_id: int, 
        message_data: Dict[str, Any], 
        settings: Dict[str, Any]
    ):
        """Анализ сообщения через ИИ и сохранение результата"""
        try:
            message = message_data['message']
            template = message_data['template']
            matched_keywords = message_data['matched_keywords']
            
            # Проверяем, не анализировали ли мы уже это сообщение
            if await self._is_message_already_processed(message.get('message_id'), user_id):
                return
            
            # Отправляем в ИИ на анализ
            ai_result = await self._analyze_purchase_intent(
                message.get('text', ''), 
                template['name']
            )
            
            # Проверяем уверенность ИИ
            min_confidence = settings.get('min_ai_confidence', 7)
            if ai_result.get('confidence', 0) < min_confidence:
                logger.info(f"AI confidence {ai_result.get('confidence')} below threshold {min_confidence}")
                return
            
            # Если ИИ подтвердил намерение - сохраняем клиента
            if ai_result.get('has_intent', False):
                await self._save_potential_client(
                    user_id, message_data, ai_result
                )
                
                # Отправляем уведомление
                await self._send_notification(
                    settings.get('notification_account'), 
                    message_data, 
                    ai_result
                )
                
        except Exception as e:
            logger.error(f"Error analyzing message with AI: {e}")
    
    async def _is_message_already_processed(self, message_id: str, user_id: int) -> bool:
        """Проверить, не обрабатывали ли мы уже это сообщение"""
        if not message_id:
            return False
            
        try:
            supabase = get_supabase()
            result = supabase.table('potential_clients').select('id').eq('message_id', message_id).eq('user_id', user_id).execute()
            
            return len(result.data) > 0
            
        except Exception as e:
            logger.error(f"Error checking if message processed: {e}")
            return False
    
    async def _analyze_purchase_intent(self, message_text: str, product_name: str) -> Dict[str, Any]:
        """Анализ намерения покупки через ИИ"""
        try:
            prompt = f"""
Проанализируй сообщение на предмет РЕАЛЬНОГО намерения купить товар категории "{product_name}".

Сообщение: "{message_text}"

Определи:
1. Есть ли намерение покупки (да/нет)
2. Насколько сильное намерение (1-10, где 10 = готов купить сейчас)
3. Тип намерения

ВАЖНО: Отличай реальные намерения от упоминаний в других контекстах.

Примеры РЕАЛЬНЫХ намерений:
- "Где купить хорошие наушники?"
- "Посоветуйте наушники до 5000р"
- "Нужны беспроводные наушники для спорта"

Примеры НЕ намерений:
- "Слушаю музыку в наушниках"
- "Песня называется 'наушники'"
- "У меня сломались наушники" (без желания купить новые)

Ответь в JSON:
{{
    "has_intent": boolean,
    "confidence": number (1-10),
    "intent_type": "seeking_info|ready_to_buy|comparing",
    "explanation": "краткое объяснение решения"
}}
"""

            response = await self.openai_service.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Ты эксперт по анализу намерений покупки в текстах."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=200
            )
            
            import json
            result = json.loads(response.choices[0].message.content)
            
            logger.info(f"AI analysis result: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error in AI analysis: {e}")
            return {
                "has_intent": False,
                "confidence": 0,
                "intent_type": "unknown",
                "explanation": f"Error in analysis: {str(e)}"
            }
    
    async def _save_potential_client(
        self, 
        user_id: int, 
        message_data: Dict[str, Any], 
        ai_result: Dict[str, Any]
    ):
        """Сохранить найденного потенциального клиента"""
        try:
            message = message_data['message']
            template = message_data['template']
            
            # Извлекаем информацию об авторе
            author = message.get('sender', {})
            
            supabase = get_supabase()
            result = supabase.table('potential_clients').insert({
                'user_id': user_id,
                'message_text': message.get('text', ''),
                'message_id': message.get('message_id'),
                'chat_id': message_data['chat_id'],
                'chat_name': message.get('chat', {}).get('title', ''),
                'author_username': author.get('username'),
                'author_first_name': author.get('first_name'),
                'author_id': str(author.get('id', '')),
                'product_template_id': template['id'],
                'template_name': template['name'],
                'matched_keywords': message_data['matched_keywords'],
                'ai_confidence_score': ai_result.get('confidence'),
                'ai_intent_type': ai_result.get('intent_type'),
                'ai_explanation': ai_result.get('explanation'),
                'client_status': 'new',
                'notification_sent': False,
                'created_at': datetime.now().isoformat()
            }).execute()
            
            if result.data:
                logger.info(f"Saved potential client: {author.get('username', 'unknown')}")
            
        except Exception as e:
            logger.error(f"Error saving potential client: {e}")
    
    async def _send_notification(
        self, 
        notification_account: Optional[str], 
        message_data: Dict[str, Any], 
        ai_result: Dict[str, Any]
    ):
        """Отправить уведомление о найденном клиенте"""
        try:
            if not notification_account:
                logger.info("No notification account configured")
                return
            
            message = message_data['message']
            template = message_data['template']
            author = message.get('sender', {})
            
            # Формируем текст уведомления
            notification_text = f"""🔥 НАЙДЕН ПОТЕНЦИАЛЬНЫЙ КЛИЕНТ!

💡 Продукт: {template['name']}
📱 Сообщение: "{message.get('text', '')[:200]}..."
👤 Автор: @{author.get('username', 'unknown')} ({author.get('first_name', 'Имя не указано')})
💬 Чат: {message.get('chat', {}).get('title', 'Неизвестный чат')}
🎯 Ключевые слова: {', '.join(message_data['matched_keywords'])}
🤖 Уверенность ИИ: {ai_result.get('confidence', 0)}/10
📊 Тип намерения: {ai_result.get('intent_type', 'unknown')}
📅 Время: {datetime.now().strftime('%H:%M, %d.%m.%Y')}

👆 Переходи в чат и предлагай свой товар!"""

            # Здесь будет отправка через Telegram API
            # Пока просто логируем
            logger.info(f"NOTIFICATION: {notification_text}")
            
            # TODO: Реализовать отправку уведомления через Telegram
            
        except Exception as e:
            logger.error(f"Error sending notification: {e}")