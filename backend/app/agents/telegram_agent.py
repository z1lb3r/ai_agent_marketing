# backend/app/agents/telegram_agent.py
from agents import Agent, ModelSettings, function_tool
from typing import Dict, Any
from ..services.telegram_service import TelegramService

# Создаем агента напрямую без базового класса
def create_telegram_analyzer_agent():
    return Agent(
        name="Telegram Analyzer",
        instructions="""You are a Telegram chat analyzer. Your tasks include:
        1. Analyzing moderator performance based on response times and message quality
        2. Detecting sentiment trends in group conversations
        3. Identifying key discussion topics and potential issues
        4. Evaluating moderator effectiveness in problem resolution
        
        Always provide structured analysis with specific metrics and recommendations.""",
        model="gpt-4-turbo-preview",
        model_settings=ModelSettings(
            temperature=0.7,
            max_tokens=1000
        ),
        tools=[
            fetch_telegram_messages,
            analyze_moderator_activity,
            detect_sentiment,
            extract_key_topics
        ]
    )

# Tools остаются такими же
@function_tool
async def fetch_telegram_messages(
    context: Dict[str, Any],
    group_id: str,
    limit: int = 100
) -> str:
    """Fetch recent messages from a Telegram group"""
    telegram_service = TelegramService()
    messages = await telegram_service.get_group_messages(group_id, limit)
    return f"Fetched {len(messages)} messages from group {group_id}"