from openai import AsyncOpenAI
from typing import List, Dict, Any
import json
import logging
from ..core.config import settings

logger = logging.getLogger(__name__)

class OpenAIService:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    
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
            # Подготавливаем данные для анализа
            analysis_data = self._prepare_analysis_data(messages, moderators)
            
            # Формируем системный промпт
            system_prompt = self._build_system_prompt()
            
            # Формируем пользовательский промпт
            user_prompt = self._build_user_prompt(
                analysis_data, prompt, group_name, moderators
            )
            
            # Отправляем запрос к OpenAI
            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            # Парсим ответ
            result = self._parse_openai_response(response.choices[0].message.content)
            
            logger.info(f"Successfully analyzed {len(messages)} messages for group {group_name}")
            return result
            
        except Exception as e:
            logger.error(f"Error in OpenAI analysis: {str(e)}")
            # Возвращаем fallback результат в случае ошибки
            return self._get_fallback_result()
    
    def _prepare_analysis_data(self, messages: List[Dict[str, Any]], moderators: List[str]) -> Dict[str, Any]:
        """Подготовка данных сообщений для анализа"""
        
        # Фильтруем сообщения модераторов если указаны
        moderator_messages = []
        user_messages = []
        
        for msg in messages:
            sender_username = msg.get('sender', {}).get('username', '')
            is_moderator = any(mod.strip('@') in sender_username for mod in moderators) if moderators else False
            
            message_data = {
                'id': msg['message_id'],
                'text': msg['text'][:500],  # Ограничиваем длину для экономии токенов
                'date': msg['date'],
                'is_reply': msg['is_reply'],
                'has_media': msg['has_media']
            }
            
            if is_moderator:
                moderator_messages.append(message_data)
            else:
                user_messages.append(message_data)
        
        return {
            'moderator_messages': moderator_messages[:20],  # Ограничиваем количество
            'user_messages': user_messages[:30],
            'total_messages': len(messages),
            'moderator_count': len(moderator_messages),
            'conversation_threads': self._identify_threads(messages)
        }
    
    def _identify_threads(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Определение цепочек диалогов"""
        threads = []
        
        # Группируем сообщения по reply_to_message_id
        for msg in messages[:10]:  # Анализируем только последние 10 для экономии
            if msg['is_reply'] and msg['reply_to_message_id']:
                # Ищем исходное сообщение
                original_msg = next((m for m in messages if m['message_id'] == msg['reply_to_message_id']), None)
                if original_msg:
                    threads.append({
                        'original': {
                            'text': original_msg['text'][:200],
                            'date': original_msg['date']
                        },
                        'reply': {
                            'text': msg['text'][:200],
                            'date': msg['date']
                        }
                    })
        
        return threads[:5]  # Максимум 5 цепочек
    
    def _build_system_prompt(self) -> str:
        """Системный промпт для анализа модераторов"""
        return """Ты - эксперт по анализу коммуникаций в онлайн-сообществах. 
        Твоя задача - оценить эффективность работы модераторов на основе их сообщений и взаимодействий с пользователями.

        Анализируй по следующим критериям:
        1. Скорость ответа на вопросы пользователей
        2. Качество и полезность ответов
        3. Тон общения (дружелюбность, профессионализм)
        4. Решение конфликтов и проблем
        5. Соблюдение правил сообщества

        Верни результат СТРОГО в формате JSON:
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
    
    def _build_user_prompt(self, data: Dict[str, Any], user_prompt: str, group_name: str, moderators: List[str]) -> str:
        """Пользовательский промпт с данными для анализа"""
        
        prompt = f"""
        ГРУППА: {group_name}
        МОДЕРАТОРЫ ДЛЯ АНАЛИЗА: {', '.join(moderators) if moderators else 'Все'}
        
        КРИТЕРИИ ОЦЕНКИ:
        {user_prompt}
        
        ДАННЫЕ ДЛЯ АНАЛИЗА:
        - Всего сообщений: {data['total_messages']}
        - Сообщений от модераторов: {data['moderator_count']}
        - Цепочек диалогов: {len(data['conversation_threads'])}
        
        СООБЩЕНИЯ МОДЕРАТОРОВ:
        """
        
        for i, msg in enumerate(data['moderator_messages'][:10]):
            prompt += f"\n{i+1}. [{msg['date']}] {msg['text']}"
        
        if data['conversation_threads']:
            prompt += "\n\nПРИМЕРЫ ДИАЛОГОВ:"
            for i, thread in enumerate(data['conversation_threads']):
                prompt += f"\n\nДиалог {i+1}:"
                prompt += f"\nВопрос: {thread['original']['text']}"
                prompt += f"\nОтвет: {thread['reply']['text']}"
        
        prompt += f"\n\nПроанализируй эффективность модераторов согласно указанным критериям и верни результат в JSON формате."
        
        return prompt
    
    def _parse_openai_response(self, response_text: str) -> Dict[str, Any]:
        """Парсинг ответа от OpenAI"""
        try:
            # Ищем JSON в ответе
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx != -1 and end_idx != 0:
                json_str = response_text[start_idx:end_idx]
                result = json.loads(json_str)
                
                # Валидируем структуру
                if self._validate_result_structure(result):
                    return result
            
            # Если парсинг не удался, возвращаем fallback
            logger.warning("Failed to parse OpenAI response, using fallback")
            return self._get_fallback_result()
            
        except Exception as e:
            logger.error(f"Error parsing OpenAI response: {e}")
            return self._get_fallback_result()
    
    def _validate_result_structure(self, result: Dict[str, Any]) -> bool:
        """Валидация структуры результата"""
        required_keys = ['summary', 'moderator_metrics', 'key_topics', 'recommendations']
        return all(key in result for key in required_keys)
    
    def _get_fallback_result(self) -> Dict[str, Any]:
        """Fallback результат в случае ошибки"""
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
                "Попробуйте запустить анализ позже"
            ]
        }
    
    async def analyze_community_sentiment(
        self,
        messages: List[Dict[str, Any]],
        prompt: str = None,
        group_name: str = "Unknown"
    ) -> Dict[str, Any]:
        """
        Анализ настроений жителей и проблем ЖКХ
        """
        try:
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
            
            # Подготавливаем данные сообщений
            message_texts = []
            for msg in messages[:50]:  # Анализируем последние 50 сообщений
                if msg.get('text') and len(msg['text']) > 10:
                    message_texts.append({
                        'text': msg['text'][:300],  # Ограничиваем длину
                        'date': msg.get('date', '')
                    })
            
            # Пользовательский промпт
            if not prompt:
                prompt = "Проанализируй настроения жителей и выяви основные проблемы в жилом комплексе"
                
            user_prompt = f"""
            ГРУППА: {group_name}
            ЗАДАЧА: {prompt}
            
            СООБЩЕНИЯ ЖИТЕЛЕЙ ({len(message_texts)} шт.):
            """
            
            for i, msg in enumerate(message_texts[:20]):  # Показываем только 20 для экономии токенов
                user_prompt += f"\n{i+1}. [{msg['date']}] {msg['text']}"
            
            user_prompt += "\n\nПроанализируй настроения и проблемы жителей согласно указанным критериям."
            
            # Запрос к OpenAI
            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            # Парсим ответ
            result = self._parse_community_response(response.choices[0].message.content)
            
            logger.info(f"Community sentiment analysis completed for {group_name}")
            return result
            
        except Exception as e:
            logger.error(f"Error in community sentiment analysis: {str(e)}")
            return self._get_community_fallback_result()

    def _get_community_fallback_result(self) -> Dict[str, Any]:
        """Fallback для анализа сообщества"""
        return {
            "sentiment_summary": {
                "overall_mood": "mock data",
                "satisfaction_score": 00,
                "complaint_level": "mock data"
            },
            "main_issues": [
                {"category": "ЖКХ", "issue": "mock data", "frequency": 1}
            ],
            "service_quality": {
                "управляющая_компания": 00,
                "коммунальные_службы": 00,
                "уборка": 00,
                "безопасность": 00
            },
            "improvement_suggestions": ["mock data"],
            "key_topics": ["общие вопросы"],
            "urgent_issues": []
        }
    
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
                    logger.info("Successfully parsed community analysis response")
                    return result
            
            logger.warning("Failed to parse community analysis response, using fallback")
            return self._get_community_fallback_result()
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error in community analysis response: {e}")
            return self._get_community_fallback_result()
        except Exception as e:
            logger.error(f"Error parsing community analysis response: {e}")
            return self._get_community_fallback_result()

    def _validate_community_structure(self, result: Dict[str, Any]) -> bool:
        """Валидация структуры результата анализа сообщества"""
        try:
            # Проверяем основные ключи
            required_keys = ['sentiment_summary', 'main_issues', 'service_quality', 'improvement_suggestions', 'key_topics', 'urgent_issues']
            
            if not all(key in result for key in required_keys):
                logger.warning(f"Missing required keys in community analysis result. Expected: {required_keys}, Got: {list(result.keys())}")
                return False
            
            # Проверяем структуру sentiment_summary
            sentiment_summary = result.get('sentiment_summary', {})
            sentiment_required = ['overall_mood', 'satisfaction_score', 'complaint_level']
            if not all(key in sentiment_summary for key in sentiment_required):
                logger.warning(f"Invalid sentiment_summary structure. Expected: {sentiment_required}, Got: {list(sentiment_summary.keys())}")
                return False
            
            # Проверяем что main_issues это список
            if not isinstance(result.get('main_issues', []), list):
                logger.warning("main_issues should be a list")
                return False
            
            # Проверяем структуру service_quality
            service_quality = result.get('service_quality', {})
            if not isinstance(service_quality, dict):
                logger.warning("service_quality should be a dictionary")
                return False
            
            # Проверяем что остальные поля это списки
            list_fields = ['improvement_suggestions', 'key_topics', 'urgent_issues']
            for field in list_fields:
                if not isinstance(result.get(field, []), list):
                    logger.warning(f"{field} should be a list")
                    return False
            
            logger.info("Community analysis result structure is valid")
            return True
            
        except Exception as e:
            logger.error(f"Error validating community analysis structure: {e}")
            return False


