# backend/app/services/scheduler_service.py
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
import logging
from datetime import datetime

from ..core.database import supabase_client
from .client_monitoring_service import ClientMonitoringService

logger = logging.getLogger(__name__)

class SchedulerService:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.monitoring_service = ClientMonitoringService()
        
    def start(self):
        """Запустить планировщик"""
        try:
            # Добавляем задачу мониторинга клиентов
            self.scheduler.add_job(
                func=self._monitor_all_users,
                trigger=IntervalTrigger(minutes=1),  # Проверяем каждую минуту
                id='client_monitoring',
                name='Client Monitoring Task',
                replace_existing=True
            )
            
            self.scheduler.start()
            logger.info("Scheduler started successfully")
            
        except Exception as e:
            logger.error(f"Error starting scheduler: {e}")
            raise
    
    def stop(self):
        """Остановить планировщик"""
        try:
            self.scheduler.shutdown()
            logger.info("Scheduler stopped")
        except Exception as e:
            logger.error(f"Error stopping scheduler: {e}")
    
    async def _monitor_all_users(self):
        """Проверить всех пользователей на необходимость мониторинга"""
        try:
            logger.debug("Running scheduled client monitoring check")
            
            # Получаем всех пользователей с активным мониторингом
            active_users = await self._get_active_monitoring_users()
            
            for user_data in active_users:
                user_id = user_data['user_id']
                settings = user_data
                
                # Проверяем, пора ли запускать мониторинг для этого пользователя
                if self._should_run_monitoring(settings):
                    logger.info(f"Running monitoring for user {user_id}")
                    
                    # Запускаем мониторинг в фоне
                    await self._run_monitoring_for_user(user_id, settings)
                    
        except Exception as e:
            logger.error(f"Error in scheduled monitoring: {e}")
    
    async def _get_active_monitoring_users(self) -> list:
        """Получить всех пользователей с активным мониторингом"""
        try:
            result = supabase_client.table('monitoring_settings').select('*').eq('is_active', True).execute()
            
            return result.data or []
            
        except Exception as e:
            logger.error(f"Error getting active monitoring users: {e}")
            return []
    
    def _should_run_monitoring(self, settings: dict) -> bool:
        """Проверить, нужно ли запускать мониторинг для пользователя"""
        try:
            # Проверяем интервал
            last_check = settings.get('last_monitoring_check')
            interval_minutes = settings.get('check_interval_minutes', 5)
            
            if last_check:
                last_check_time = datetime.fromisoformat(last_check)
                time_diff = (datetime.now() - last_check_time).total_seconds() / 60
                
                if time_diff < interval_minutes:
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking if should run monitoring: {e}")
            return False
    
    async def _run_monitoring_for_user(self, user_id: int, settings: dict):
        """Запустить мониторинг для конкретного пользователя"""
        try:
            # Обновляем время последней проверки
            await self._update_last_check_time(user_id)
            
            # Получаем шаблоны продуктов
            templates = await self._get_user_templates(user_id)
            if not templates:
                logger.info(f"No templates for user {user_id}")
                return
            
            # Получаем чаты для мониторинга
            monitored_chats = settings.get('monitored_chats', [])
            if not monitored_chats:
                logger.info(f"No monitored chats for user {user_id}")
                return
            
            # Запускаем поиск и анализ
            await self.monitoring_service._search_and_analyze(user_id, settings)
            
        except Exception as e:
            logger.error(f"Error running monitoring for user {user_id}: {e}")
    
    async def _update_last_check_time(self, user_id: int):
        """Обновить время последней проверки"""
        try:
            supabase_client.table('monitoring_settings').update({
                'last_monitoring_check': datetime.now().isoformat()
            }).eq('user_id', user_id).execute()
            
        except Exception as e:
            logger.error(f"Error updating last check time: {e}")
    
    async def _get_user_templates(self, user_id: int) -> list:
        """Получить шаблоны пользователя"""
        try:
            result = supabase_client.table('product_templates').select('*').eq('user_id', user_id).eq('is_active', True).execute()
            
            return result.data or []
            
        except Exception as e:
            logger.error(f"Error getting user templates: {e}")
            return []

# Глобальный экземпляр планировщика
scheduler_service = SchedulerService()