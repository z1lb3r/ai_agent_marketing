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
            result = supabase_client.table('monitoring_settings').select('*').eq('user_id', user_id).execute()
            
            if result.data:
                return result.data[0]
            return None
            
        except Exception as e:
            logger.error(f"Error getting user settings for {user_id}: {e}")
            return None

    
    async def _search_and_analyze(self, user_id: int, settings: Dict[str, Any]):
        """Поиск ключевых слов и анализ найденных сообщений"""
        try:
            # Получаем шаблоны продуктов пользователя
            templates = await self._get_user_templates(user_id)
            if not templates:
                logger.info(f"No templates for user {user_id}")
                return
            
            # Получаем чаты для мониторинга
            monitored_chats = settings.get('monitored_chats', [])
            if not monitored_chats:
                logger.info(f"No monitored chats for user {user_id}")
                return
            
            # Получаем настройки
            lookback_minutes = settings.get('lookback_minutes', 5)
            min_ai_confidence = settings.get('min_ai_confidence', 7)
            
            # Для каждого чата ищем новые сообщения
            for chat_id in monitored_chats:
                try:
                    # Получаем последние сообщения из чата
                    recent_messages = await self._get_recent_messages(chat_id, lookback_minutes)
                    
                    # Для каждого шаблона ищем ключевые слова
                    for template in templates:
                        keywords = template.get('keywords', [])
                        if not keywords:
                            continue
                        
                        # Ищем сообщения с ключевыми словами
                        for message in recent_messages:
                            message_text = message.get('text', '')
                            matched_keywords = self._find_keywords_in_text(message_text, keywords)
                            
                            if matched_keywords:
                                # Подготавливаем данные для анализа ИИ
                                message_data = {
                                    'message': message,
                                    'template': template,
                                    'matched_keywords': matched_keywords
                                }
                                
                                # Анализируем через ИИ
                                await self._analyze_message_with_ai(user_id, message_data, settings)
                
                except Exception as e:
                    logger.error(f"Error processing chat {chat_id}: {e}")
                    continue
            
        except Exception as e:
            logger.error(f"Error in search and analyze: {e}")
    
    async def _get_user_templates(self, user_id: int) -> List[Dict[str, Any]]:
        """Получить активные шаблоны пользователя"""
        try:
            result = supabase_client.table('product_templates').select('*').eq('user_id', user_id).eq('is_active', True).execute()
            
            return result.data or []
            
        except Exception as e:
            logger.error(f"Error getting user templates: {e}")
            return []
    
    async def _get_recent_messages(self, chat_id: str, lookback_minutes: int) -> List[Dict[str, Any]]:
        """Получить последние сообщения из чата"""
        try:
            # Рассчитываем время для поиска сообщений
            lookback_days = max(1, lookback_minutes // (24 * 60))  # Минимум 1 день
            
            # Получаем сообщения через Telegram service
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
            
            # Создаем промпт для ИИ анализа
            ai_prompt = f"""
            Проанализируй сообщение пользователя на предмет намерения купить товар/услугу.
            
            Продукт: {template['name']}
            Ключевые слова: {', '.join(template['keywords'])}
            Сообщение: "{message.get('text', '')}"
            Найденные ключевые слова: {', '.join(matched_keywords)}
            
            Оцени по шкале от 1 до 10:
            1. Уверенность в том, что это потенциальный покупатель
            2. Тип намерения (поиск информации, готовность к покупке, сравнение вариантов)
            
            Ответь в формате JSON:
            {{
                "confidence": число от 1 до 10,
                "intent_type": "информация/покупка/сравнение/другое",
                "reasoning": "объяснение анализа"
            }}
            """
            
            # Отправляем запрос к ИИ (здесь используется заглушка)
            ai_result = await self._call_ai_analysis(ai_prompt)
            
            # Проверяем минимальную уверенность
            min_confidence = settings.get('min_ai_confidence', 7)
            if ai_result.get('confidence', 0) >= min_confidence:
                # Сохраняем потенциального клиента
                await self._save_potential_client(user_id, message_data, ai_result)
                
                # Отправляем уведомление
                notification_account = settings.get('notification_account')
                await self._send_notification(notification_account, message_data, ai_result)
            
        except Exception as e:
            logger.error(f"Error analyzing message with AI: {e}")
    
    async def _is_message_already_processed(self, message_id: str, user_id: int) -> bool:
        """Проверить, обрабатывалось ли уже это сообщение"""
        try:
            if not message_id:
                return False
            
            result = supabase_client.table('potential_clients').select('id').eq('message_id', message_id).eq('user_id', user_id).execute()
            
            return bool(result.data)
            
        except Exception as e:
            logger.error(f"Error checking if message processed: {e}")
            return False
    
    async def _call_ai_analysis(self, prompt: str) -> Dict[str, Any]:
        """Вызов ИИ для анализа (заглушка)"""
        try:
            # TODO: Реализовать реальный вызов OpenAI API
            # Сейчас возвращаем заглушку
            return {
                "confidence": 8,
                "intent_type": "покупка",
                "reasoning": "Пользователь явно ищет товар и готов к покупке"
            }
            
        except Exception as e:
            logger.error(f"Error calling AI analysis: {e}")
            return {"confidence": 0, "intent_type": "unknown", "reasoning": "Ошибка анализа"}
    
    async def _save_potential_client(
        self, 
        user_id: int, 
        message_data: Dict[str, Any], 
        ai_result: Dict[str, Any]
    ):
        """Сохранить потенциального клиента в базу данных"""
        try:
            message = message_data['message']
            template = message_data['template']
            author = message.get('sender', {})
            
            # Подготавливаем данные для сохранения
            client_data = {
                'user_id': user_id,
                'product_template_id': template.get('id'),
                'message_id': message.get('message_id'),
                'chat_id': message.get('chat', {}).get('id'),
                'chat_title': message.get('chat', {}).get('title'),
                'author_username': author.get('username'),
                'author_first_name': author.get('first_name'),
                'author_telegram_id': author.get('id'),
                'message_text': message.get('text', '')[:1000],  # Ограничиваем длину
                'matched_keywords': message_data['matched_keywords'],
                'ai_confidence': ai_result.get('confidence', 0),
                'ai_intent_type': ai_result.get('intent_type', 'unknown'),
                'ai_reasoning': ai_result.get('reasoning', ''),
                'client_status': 'new',
                'notification_sent': False,
                'created_at': datetime.now().isoformat()
            }
            
            result = supabase_client.table('potential_clients').insert(client_data).execute()
            
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