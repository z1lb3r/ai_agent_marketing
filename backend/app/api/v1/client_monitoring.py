# backend/app/api/v1/client_monitoring.py
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel
import logging

from ...core.database import supabase_client
from ...services.client_monitoring_service import ClientMonitoringService

logger = logging.getLogger(__name__)

router = APIRouter()

# Pydantic модели для валидации
class ProductTemplateCreate(BaseModel):
    name: str
    keywords: List[str]

class ProductTemplateUpdate(BaseModel):
    name: Optional[str] = None
    keywords: Optional[List[str]] = None
    is_active: Optional[bool] = None

class MonitoringSettingsUpdate(BaseModel):
    monitored_chats: Optional[List[str]] = None
    notification_account: Optional[str] = None
    check_interval_minutes: Optional[int] = 5
    lookback_minutes: Optional[int] = 5
    min_ai_confidence: Optional[int] = 7
    is_active: Optional[bool] = None

class ClientStatusUpdate(BaseModel):
    status: str  # 'new', 'contacted', 'ignored', 'converted'

# Инициализируем сервис мониторинга
monitoring_service = ClientMonitoringService()

# ==================== PRODUCT TEMPLATES ====================

@router.post("/product-templates")
async def create_product_template(template: ProductTemplateCreate, user_id: int = 1):
    """Создать новый шаблон продукта"""
    try:
        # Валидация
        if not template.keywords:
            raise HTTPException(status_code=400, detail="Keywords list cannot be empty")
        
        # Создаем запись
        result = supabase_client.table('product_templates').insert({
            'user_id': user_id,
            'name': template.name,
            'keywords': template.keywords,
            'is_active': True,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }).execute()
        
        if result.data:
            logger.info(f"Created product template: {template.name}")
            return {"status": "success", "data": result.data[0]}
        else:
            raise HTTPException(status_code=400, detail="Failed to create template")
            
    except Exception as e:
        logger.error(f"Error creating product template: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/product-templates")
async def get_product_templates(user_id: int = 1):
    """Получить все шаблоны продуктов пользователя"""
    try:
        result = supabase_client.table('product_templates').select('*').eq('user_id', user_id).order('created_at', desc=True).execute()
        
        return {"status": "success", "data": result.data}
        
    except Exception as e:
        logger.error(f"Error fetching product templates: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/product-templates/{template_id}")
async def update_product_template(template_id: int, template: ProductTemplateUpdate, user_id: int = 1):
    """Обновить шаблон продукта"""
    try:
        # Подготавливаем данные для обновления
        update_data = {
            'updated_at': datetime.now().isoformat()
        }
        
        if template.name is not None:
            update_data['name'] = template.name
        if template.keywords is not None:
            if not template.keywords:
                raise HTTPException(status_code=400, detail="Keywords list cannot be empty")
            update_data['keywords'] = template.keywords
        if template.is_active is not None:
            update_data['is_active'] = template.is_active
        
        result = supabase_client.table('product_templates').update(update_data).eq('id', template_id).eq('user_id', user_id).execute()
        
        if result.data:
            logger.info(f"Updated product template {template_id}")
            return {"status": "success", "data": result.data[0]}
        else:
            raise HTTPException(status_code=404, detail="Template not found")
            
    except Exception as e:
        logger.error(f"Error updating product template: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/product-templates/{template_id}")
async def delete_product_template(template_id: int, user_id: int = 1):
    """Удалить шаблон продукта"""
    try:
        result = supabase_client.table('product_templates').delete().eq('id', template_id).eq('user_id', user_id).execute()
        
        if result.data:
            logger.info(f"Deleted product template {template_id}")
            return {"status": "success", "message": "Template deleted"}
        else:
            raise HTTPException(status_code=404, detail="Template not found")
            
    except Exception as e:
        logger.error(f"Error deleting product template: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== MONITORING SETTINGS ====================

@router.get("/monitoring/settings")
async def get_monitoring_settings(user_id: int = 1):
    """Получить настройки мониторинга пользователя"""
    try:
        result = supabase_client.table('monitoring_settings').select('*').eq('user_id', user_id).execute()
        
        if result.data:
            return {"status": "success", "data": result.data[0]}
        else:
            # Создаем настройки по умолчанию, если их нет
            default_settings = {
                'user_id': user_id,
                'monitored_chats': [],
                'notification_account': '',
                'check_interval_minutes': 5,
                'lookback_minutes': 5,
                'min_ai_confidence': 7,
                'is_active': False,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            create_result = supabase_client.table('monitoring_settings').insert(default_settings).execute()
            return {"status": "success", "data": create_result.data[0]}
            
    except Exception as e:
        logger.error(f"Error fetching monitoring settings: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/monitoring/settings")
async def update_monitoring_settings(settings: MonitoringSettingsUpdate, user_id: int = 1):
    """Обновить настройки мониторинга"""
    try:
        # Подготавливаем данные для обновления
        update_data = {
            'updated_at': datetime.now().isoformat()
        }
        
        if settings.monitored_chats is not None:
            update_data['monitored_chats'] = settings.monitored_chats
        if settings.notification_account is not None:
            update_data['notification_account'] = settings.notification_account
        if settings.check_interval_minutes is not None:
            update_data['check_interval_minutes'] = settings.check_interval_minutes
        if settings.lookback_minutes is not None:
            update_data['lookback_minutes'] = settings.lookback_minutes
        if settings.min_ai_confidence is not None:
            update_data['min_ai_confidence'] = settings.min_ai_confidence
        if settings.is_active is not None:
            update_data['is_active'] = settings.is_active
        
        # Обновляем или создаем настройки
        result = supabase_client.table('monitoring_settings').update(update_data).eq('user_id', user_id).execute()
        
        if result.data:
            logger.info(f"Updated monitoring settings for user {user_id}")
            return {"status": "success", "data": result.data[0]}
        else:
            raise HTTPException(status_code=404, detail="Settings not found")
            
    except Exception as e:
        logger.error(f"Error updating monitoring settings: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/monitoring/start")
async def start_monitoring(user_id: int = 1):
    """Запустить мониторинг для пользователя"""
    try:
        # Включаем мониторинг в настройках
        await update_monitoring_settings(MonitoringSettingsUpdate(is_active=True), user_id)
        
        # Запускаем сервис мониторинга
        await monitoring_service.start_monitoring(user_id)
        
        logger.info(f"Started monitoring for user {user_id}")
        return {"status": "success", "message": "Monitoring started"}
        
    except Exception as e:
        logger.error(f"Error starting monitoring: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/monitoring/stop")
async def stop_monitoring(user_id: int = 1):
    """Остановить мониторинг для пользователя"""
    try:
        # Выключаем мониторинг в настройках
        await update_monitoring_settings(MonitoringSettingsUpdate(is_active=False), user_id)
        
        # Останавливаем сервис мониторинга
        await monitoring_service.stop_monitoring(user_id)
        
        logger.info(f"Stopped monitoring for user {user_id}")
        return {"status": "success", "message": "Monitoring stopped"}
        
    except Exception as e:
        logger.error(f"Error stopping monitoring: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== POTENTIAL CLIENTS ====================

@router.get("/potential-clients")
async def get_potential_clients(
    user_id: int = 1,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
):
    """Получить список найденных потенциальных клиентов"""
    try:
        query = supabase_client.table('potential_clients').select('*').eq('user_id', user_id)
        
        if status:
            query = query.eq('client_status', status)
        
        result = query.order('created_at', desc=True).range(offset, offset + limit - 1).execute()
        
        return {"status": "success", "data": result.data}
        
    except Exception as e:
        logger.error(f"Error fetching potential clients: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/potential-clients/{client_id}/status")
async def update_client_status(client_id: int, status_update: ClientStatusUpdate, user_id: int = 1):
    """Обновить статус потенциального клиента"""
    try:
        # Валидация статуса
        valid_statuses = ['new', 'contacted', 'ignored', 'converted']
        if status_update.status not in valid_statuses:
            raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")
        
        result = supabase_client.table('potential_clients').update({
            'client_status': status_update.status
        }).eq('id', client_id).eq('user_id', user_id).execute()
        
        if result.data:
            logger.info(f"Updated client {client_id} status to {status_update.status}")
            return {"status": "success", "data": result.data[0]}
        else:
            raise HTTPException(status_code=404, detail="Client not found")
            
    except Exception as e:
        logger.error(f"Error updating client status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/monitoring/stats")
async def get_monitoring_stats(user_id: int = 1):
    """Получить статистику мониторинга"""
    try:
        # Общее количество найденных клиентов
        total_result = supabase_client.table('potential_clients').select('id', count='exact').eq('user_id', user_id).execute()
        total_clients = total_result.count or 0
        
        # Количество по статусам
        status_stats = {}
        for status in ['new', 'contacted', 'ignored', 'converted']:
            status_result = supabase_client.table('potential_clients').select('id', count='exact').eq('user_id', user_id).eq('client_status', status).execute()
            status_stats[status] = status_result.count or 0
        
        # Статистика за последние 7 дней
        from datetime import datetime, timedelta
        week_ago = (datetime.now() - timedelta(days=7)).isoformat()
        week_result = supabase_client.table('potential_clients').select('id', count='exact').eq('user_id', user_id).gte('created_at', week_ago).execute()
        clients_this_week = week_result.count or 0
        
        return {
            "status": "success",
            "data": {
                "total_clients": total_clients,
                "clients_this_week": clients_this_week,
                "status_distribution": status_stats
            }
        }
        
    except Exception as e:
        logger.error(f"Error fetching monitoring stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))