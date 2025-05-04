# backend/app/api/v1/telegram.py
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any
from ...services.telegram_service import TelegramService
from ...core.database import supabase_client
from ...agents.telegram_agent import create_telegram_analyzer_agent
from agents import Runner

router = APIRouter()

@router.get("/groups")
async def get_groups():
    """Получить список отслеживаемых групп"""
    try:
        response = supabase_client.table('telegram_groups').select("*").execute()
        return response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/groups/{group_id}/analyze")
async def analyze_group(group_id: str):
    """Запустить анализ группы"""
    try:
        # Создаем агента
        agent = create_telegram_analyzer_agent()
        
        # Запускаем анализ
        result = await Runner.run(
            starting_agent=agent,
            input=f"Analyze Telegram group {group_id} and provide moderator performance metrics",
            context={"group_id": group_id}
        )
        
        # Сохраняем результаты
        await save_analysis_results(group_id, result.final_output)
        
        return {"status": "success", "result": result.final_output}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def save_analysis_results(group_id: str, results: Dict[str, Any]):
    """Сохранить результаты анализа"""
    try:
        supabase_client.table('analysis_reports').insert({
            'group_id': group_id,
            'type': 'telegram_analysis',
            'results': results
        }).execute()
    except Exception as e:
        logger.error(f"Failed to save analysis results: {e}")