# backend/app/services/openai_service.py
from openai import AsyncOpenAI
from typing import List, Dict, Any, Optional
import json
import logging
import asyncio
from ..core.config import settings

logger = logging.getLogger(__name__)

class OpenAIService:
    def __init__(self):
        """Инициализация OpenAI сервиса с проверками и таймаутами"""
        
        # Проверяем наличие API ключа
        if not settings.OPENAI_API_KEY:
            logger.error("❌ OPENAI_API_KEY not configured!")
            raise ValueError("OPENAI_API_KEY must be set in environment variables")
        
        if not settings.OPENAI_API_KEY.startswith('sk-'):
            logger.error("❌ Invalid OPENAI_API_KEY format!")
            raise ValueError("OPENAI_API_KEY must start with 'sk-'")
        
        logger.info("✅ OpenAI service initialized")
        self.client = AsyncOpenAI(
            api_key=settings.OPENAI_API_KEY,
            timeout=45.0  # Глобальный таймаут для всех запросов
        )
    
    async def analyze_moderator_performance(
        self,
        messages: List[Dict[str, Any]],
        prompt: str,
        moderators: List[str] = None,
        group_name: str = "Unknown"
    ) -> Dict[str, Any]:
        """
        Анализ эффективности модераторов через OpenAI
        
        Args:
            messages: Список сообщений из группы
            prompt: Критерии оценки от пользователя
            moderators: Список модераторов для анализа
            group_name: Название группы
            
        Returns:
            Результат анализа в структурированном виде
        """
        try:
            logger.info(f"🤖 Starting moderator analysis for group: {group_name}")
            
            # Проверяем входные данные
            if not messages:
                logger.warning("❌ No messages provided for analysis")
                return self._get_moderator_fallback_result()
            
            if not prompt or not prompt.strip():
                logger.warning("❌ No prompt provided for analysis")
                return self._get_moderator_fallback_result()
            
            # Подготавливаем данные для анализа
            analysis_data = self._prepare_moderator_analysis_data(messages, moderators)
            
            # Формируем системный промпт
            system_prompt = self._build_moderator_system_prompt()
            
            # Формируем пользовательский промпт
            user_prompt = self._build_moderator_user_prompt(
                analysis_data, prompt, group_name, moderators
            )
            
            logger.info("📤 Sending request to OpenAI...")
            
            # Отправляем запрос к OpenAI с таймаутом
            response = await asyncio.wait_for(
                self.client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.7,
                    max_tokens=2000
                ),
                timeout=45.0
            )
            
            logger.info("✅ Received response from OpenAI")
            
            # Парсим ответ
            result = self._parse_moderator_response(response.choices[0].message.content)
            
            logger.info("✅ Moderator analysis completed successfully")
            return result
            
        except asyncio.TimeoutError:
            logger.error("⏰ OpenAI request timed out for moderator analysis")
            return self._get_moderator_fallback_result()
        except Exception as e:
            logger.error(f"💥 Error in moderator analysis: {str(e)}")
            return self._get_moderator_fallback_result()

    async def analyze_community_sentiment(
        self,
        messages: List[Dict[str, Any]],
        prompt: str = None,
        group_name: str = "Unknown"
    ) -> Dict[str, Any]:
        """
        Анализ настроений жителей и проблем ЖКХ
        
        Args:
            messages: Список сообщений из группы
            prompt: Критерии анализа от пользователя
            group_name: Название группы
            
        Returns:
            Результат анализа настроений сообщества
        """
        try:
            logger.info(f"🏠 Starting community sentiment analysis for group: {group_name}")
            
            # Проверяем входные данные
            if not messages:
                logger.warning("❌ No messages provided for community analysis")
                return self._get_community_fallback_result()
            
            # Системный промпт для анализа жителей ЖКХ
            system_prompt = """Ты - эксперт по анализу общественных настроений в жилых комплексах и районах.

Анализируй сообщения жителей для выявления:
            
1. Основные проблемы и жалобы
2. Качество работы управляющих компаний и коммунальных служб  
3. Общие настроения жителей
4. Предложения по улучшениям
5. Проблемные зоны (подъезды, дворы, инфраструктура)

Верни результат СТРОГО в JSON формате:
{
    "sentiment_summary": {
        "overall_mood": "недовольны|нейтрально|довольны",
        "satisfaction_score": number (0-100),
        "complaint_level": "низкий|средний|высокий"
    },
    "main_issues": [
        {"category": "ЖКХ|Двор|Подъезд|Парковка|Шум|Безопасность", "issue": "описание", "frequency": number}
    ],
    "service_quality": {
        "управляющая_компания": number (0-100),
        "коммунальные_службы": number (0-100), 
        "уборка": number (0-100),
        "безопасность": number (0-100)
    },
    "improvement_suggestions": [string],
    "key_topics": [string],
    "urgent_issues": [string]
}"""
            
            # Подготавливаем данные сообщений (ограничиваем для экономии токенов)
            message_texts = []
            for msg in messages[:100]:  # Максимум 100 сообщений
                if msg.get('text') and len(msg['text'].strip()) > 5:
                    message_texts.append({
                        'text': msg['text'][:500],  # Ограничиваем длину сообщения
                        'date': msg.get('date', '')
                    })
            
            # Пользовательский промпт
            if not prompt or not prompt.strip():
                prompt = "Проанализируй настроения жителей и выяви основные проблемы в жилом комплексе"
                
            user_prompt = f"""
ГРУППА: {group_name}
ЗАДАЧА: {prompt}

СООБЩЕНИЯ ЖИТЕЛЕЙ ({len(message_texts)} шт.):
"""
            
            # Добавляем сообщения (максимум 30 для экономии токенов)
            for i, msg in enumerate(message_texts[:30]):
                user_prompt += f"\n{i+1}. [{msg['date']}] {msg['text']}"
            
            if len(message_texts) > 30:
                user_prompt += f"\n... и еще {len(message_texts) - 30} сообщений"
            
            user_prompt += "\n\nПроанализируй настроения и проблемы жителей согласно указанным критериям."
            
            logger.info("📤 Sending community analysis request to OpenAI...")
            
            # Запрос к OpenAI с таймаутом
            response = await asyncio.wait_for(
                self.client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.7,
                    max_tokens=2000
                ),
                timeout=45.0
            )
            
            logger.info("✅ Received community analysis response from OpenAI")
            
            # Парсим ответ
            result = self._parse_community_response(response.choices[0].message.content)
            
            logger.info("✅ Community sentiment analysis completed successfully")
            return result
            
        except asyncio.TimeoutError:
            logger.error("⏰ OpenAI request timed out for community analysis")
            return self._get_community_fallback_result()
        except Exception as e:
            logger.error(f"💥 Error in community sentiment analysis: {str(e)}")
            return self._get_community_fallback_result()

    def _prepare_moderator_analysis_data(
        self, 
        messages: List[Dict[str, Any]], 
        moderators: List[str] = None
    ) -> Dict[str, Any]:
        """Подготовка данных для анализа модераторов"""
        
        # Фильтруем и структурируем сообщения
        structured_messages = []
        moderator_messages = []
        
        for msg in messages:
            if msg.get('text') and len(msg['text'].strip()) > 3:
                structured_msg = {
                    'id': msg.get('message_id', ''),
                    'text': msg['text'][:300],  # Ограничиваем длину
                    'date': msg.get('date', ''),
                    'sender_id': msg.get('sender_id', ''),
                    'is_reply': msg.get('is_reply', False)
                }
                structured_messages.append(structured_msg)
                
                # Проверяем, является ли отправитель модератором
                if moderators and msg.get('sender_id') in moderators:
                    moderator_messages.append(structured_msg)
        
        return {
            'all_messages': structured_messages[:50],  # Ограничиваем количество
            'moderator_messages': moderator_messages[:20],
            'total_messages': len(structured_messages),
            'moderator_count': len(moderator_messages)
        }

    def _build_moderator_system_prompt(self) -> str:
        """Системный промпт для анализа модераторов"""
        return """Ты - эксперт по анализу эффективности модерации в онлайн-сообществах.

Анализируй работу модераторов по следующим критериям:
1. Время ответа на вопросы пользователей
2. Качество и полезность ответов
3. Тон общения (профессиональный, дружелюбный)
4. Решение конфликтов и проблем
5. Соблюдение правил сообщества

Верни результат в JSON формате:
{
    "summary": {
        "sentiment_score": number (0-100),
        "response_time_avg": number (минуты),
        "resolved_issues": number,
        "satisfaction_score": number (0-100),
        "engagement_rate": number (0-100)
    },
    "moderator_metrics": {
        "response_time": {"avg": number, "min": number, "max": number},
        "sentiment": {"positive": number, "neutral": number, "negative": number},
        "performance": {"effectiveness": number, "helpfulness": number, "clarity": number}
    },
    "key_topics": [string],
    "recommendations": [string]
}"""

    def _build_moderator_user_prompt(
        self, 
        data: Dict[str, Any], 
        prompt: str, 
        group_name: str, 
        moderators: List[str] = None
    ) -> str:
        """Пользовательский промпт для анализа модераторов"""
        
        user_prompt = f"""
ГРУППА: {group_name}
КРИТЕРИИ ОЦЕНКИ: {prompt}
МОДЕРАТОРЫ: {', '.join(moderators) if moderators else 'Не указаны'}

СТАТИСТИКА:
- Всего сообщений: {data['total_messages']}
- Сообщений от модераторов: {data['moderator_count']}

ПРИМЕРЫ СООБЩЕНИЙ:
"""
        
        # Добавляем примеры сообщений
        for i, msg in enumerate(data['all_messages'][:20]):
            msg_type = "📋 МОДЕРАТОР" if msg['sender_id'] in (moderators or []) else "👤 ПОЛЬЗОВАТЕЛЬ"
            user_prompt += f"\n{i+1}. {msg_type} [{msg['date']}]: {msg['text']}"
        
        user_prompt += f"\n\nПроанализируй эффективность модераторов согласно указанным критериям."
        
        return user_prompt

    def _parse_moderator_response(self, response_text: str) -> Dict[str, Any]:
        """Парсинг ответа от OpenAI для анализа модераторов"""
        try:
            # Ищем JSON в ответе
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx != -1 and end_idx != 0:
                json_str = response_text[start_idx:end_idx]
                result = json.loads(json_str)
                
                # Валидируем структуру
                if self._validate_moderator_structure(result):
                    logger.info("✅ Successfully parsed moderator analysis response")
                    return result
            
            logger.warning("⚠️ Failed to parse moderator analysis response, using fallback")
            return self._get_moderator_fallback_result()
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON decode error in moderator analysis response: {e}")
            return self._get_moderator_fallback_result()
        except Exception as e:
            logger.error(f"❌ Error parsing moderator analysis response: {e}")
            return self._get_moderator_fallback_result()

    def _parse_community_response(self, response_text: str) -> Dict[str, Any]:
        """Парсинг ответа от OpenAI для анализа сообщества"""
        try:
            # Ищем JSON в ответе
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx != -1 and end_idx != 0:
                json_str = response_text[start_idx:end_idx]
                result = json.loads(json_str)
                
                # Валидируем структуру для анализа сообщества
                if self._validate_community_structure(result):
                    logger.info("✅ Successfully parsed community analysis response")
                    return result
            
            logger.warning("⚠️ Failed to parse community analysis response, using fallback")
            return self._get_community_fallback_result()
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON decode error in community analysis response: {e}")
            return self._get_community_fallback_result()
        except Exception as e:
            logger.error(f"❌ Error parsing community analysis response: {e}")
            return self._get_community_fallback_result()

    def _validate_moderator_structure(self, result: Dict[str, Any]) -> bool:
        """Валидация структуры результата анализа модераторов"""
        try:
            required_keys = ['summary', 'moderator_metrics', 'key_topics', 'recommendations']
            
            if not all(key in result for key in required_keys):
                logger.warning(f"❌ Missing required keys in moderator analysis. Expected: {required_keys}")
                return False
            
            # Проверяем структуру summary
            summary = result.get('summary', {})
            summary_required = ['sentiment_score', 'response_time_avg', 'resolved_issues', 'satisfaction_score']
            if not all(key in summary for key in summary_required):
                logger.warning(f"❌ Invalid summary structure in moderator analysis")
                return False
            
            logger.info("✅ Moderator analysis result structure is valid")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error validating moderator analysis structure: {e}")
            return False

    def _validate_community_structure(self, result: Dict[str, Any]) -> bool:
        """Валидация структуры результата анализа сообщества"""
        try:
            # Проверяем основные ключи
            required_keys = ['sentiment_summary', 'main_issues', 'service_quality', 'improvement_suggestions', 'key_topics', 'urgent_issues']
            
            if not all(key in result for key in required_keys):
                logger.warning(f"❌ Missing required keys in community analysis. Expected: {required_keys}")
                return False
            
            # Проверяем структуру sentiment_summary
            sentiment_summary = result.get('sentiment_summary', {})
            sentiment_required = ['overall_mood', 'satisfaction_score', 'complaint_level']
            if not all(key in sentiment_summary for key in sentiment_required):
                logger.warning(f"❌ Invalid sentiment_summary structure")
                return False
            
            # Проверяем что main_issues это список
            if not isinstance(result.get('main_issues', []), list):
                logger.warning("❌ main_issues should be a list")
                return False
            
            # Проверяем структуру service_quality
            service_quality = result.get('service_quality', {})
            if not isinstance(service_quality, dict):
                logger.warning("❌ service_quality should be a dictionary")
                return False
            
            logger.info("✅ Community analysis result structure is valid")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error validating community analysis structure: {e}")
            return False

    def _get_moderator_fallback_result(self) -> Dict[str, Any]:
        """Fallback результат для анализа модераторов"""
        return {
            "summary": {
                "sentiment_score": 75,
                "response_time_avg": 5.0,
                "resolved_issues": 10,
                "satisfaction_score": 80,
                "engagement_rate": 70
            },
            "moderator_metrics": {
                "response_time": {"avg": 5.0, "min": 1.0, "max": 15.0},
                "sentiment": {"positive": 60, "neutral": 30, "negative": 10},
                "performance": {"effectiveness": 75, "helpfulness": 80, "clarity": 70}
            },
            "key_topics": ["support", "general discussion", "questions"],
            "recommendations": [
                "Анализ временно недоступен - используются базовые метрики",
                "Попробуйте запустить анализ позже",
                "Проверьте подключение к OpenAI API"
            ]
        }

    def _get_community_fallback_result(self) -> Dict[str, Any]:
        """Fallback результат для анализа сообщества"""
        return {
            "sentiment_summary": {
                "overall_mood": "анализ недоступен",
                "satisfaction_score": 0,
                "complaint_level": "неопределен"
            },
            "main_issues": [
                {"category": "Техническая", "issue": "Анализ временно недоступен", "frequency": 1}
            ],
            "service_quality": {
                "управляющая_компания": 0,
                "коммунальные_службы": 0,
                "уборка": 0,
                "безопасность": 0
            },
            "improvement_suggestions": [
                "Попробуйте анализ позже",
                "Проверьте настройки OpenAI API",
                "Уменьшите количество дней для анализа"
            ],
            "key_topics": ["техническая проблема"],
            "urgent_issues": ["Система анализа временно недоступна"]
        }

    async def test_connection(self) -> Dict[str, Any]:
        """Тестирование подключения к OpenAI API"""
        try:
            logger.info("🧪 Testing OpenAI API connection...")
            
            response = await asyncio.wait_for(
                self.client.chat.completions.create(
                    model="gpt-4",
                    messages=[{"role": "user", "content": "Test connection. Reply with 'OK'."}],
                    max_tokens=10
                ),
                timeout=30.0
            )
            
            logger.info("✅ OpenAI API connection test successful")
            return {
                "status": "success",
                "message": "OpenAI API connected successfully",
                "response": response.choices[0].message.content
            }
            
        except asyncio.TimeoutError:
            logger.error("⏰ OpenAI API connection test timed out")
            return {
                "status": "timeout",
                "message": "OpenAI API connection timed out"
            }
        except Exception as e:
            logger.error(f"❌ OpenAI API connection test failed: {str(e)}")
            return {
                "status": "error", 
                "message": f"OpenAI API connection failed: {str(e)}"
            }