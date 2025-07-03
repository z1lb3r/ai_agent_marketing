# backend/app/services/scheduler_service.py
import asyncio
import logging
from datetime import datetime, timezone

from ..core.database import supabase_client
from .client_monitoring_service import ClientMonitoringService

logger = logging.getLogger(__name__)

class SchedulerService:
    def __init__(self):
        self.monitoring_service = ClientMonitoringService()
        self.task = None
        self.running = False
        
    def start(self):
        """Запустить планировщик"""
        try:
            if self.running:
                logger.warning("Scheduler already running")
                return
                
            logger.info("Starting scheduler with asyncio approach...")
            
            # Создаем asyncio task для мониторинга
            self.task = asyncio.create_task(self._monitoring_loop())
            self.running = True
            
            logger.info("Scheduler started successfully")
            
        except Exception as e:
            logger.error(f"Error starting scheduler: {e}")
            raise
    
    def stop(self):
        """Остановить планировщик"""
        try:
            if not self.running:
                return
                
            logger.info("Stopping scheduler...")
            self.running = False
            
            if self.task and not self.task.done():
                self.task.cancel()
                
            logger.info("Scheduler stopped")
            
        except Exception as e:
            logger.error(f"Error stopping scheduler: {e}")
    
    async def _monitoring_loop(self):
        """Основной цикл мониторинга (запускается каждую минуту)"""
        logger.info("🚀 SCHEDULER: Monitoring loop started")
        
        while self.running:
            try:
                # Выполняем мониторинг
                await self._monitor_all_users()
                
                # Ждем 60 секунд до следующей проверки
                await asyncio.sleep(60)
                
            except asyncio.CancelledError:
                logger.info("📴 SCHEDULER: Monitoring loop cancelled")
                break
            except Exception as e:
                logger.error(f"❌ SCHEDULER: Error in monitoring loop: {e}")
                # При ошибке ждем 30 секунд и продолжаем
                await asyncio.sleep(30)
    
    async def _monitor_all_users(self):
        """Проверить всех пользователей на необходимость мониторинга"""
        try:
            logger.info("🔍 SCHEDULER: Running scheduled client monitoring check")
            
            # Получаем всех пользователей с активным мониторингом
            active_users = await self._get_active_monitoring_users()
            
            if not active_users:
                logger.warning("❌ SCHEDULER: No active monitoring users found")
                return
            
            logger.info(f"✅ SCHEDULER: Found {len(active_users)} active monitoring users")
            
            for user_data in active_users:
                user_id = user_data['user_id']
                settings = user_data
                
                logger.info(f"🔍 SCHEDULER: Checking monitoring for user {user_id}")
                
                # Проверяем, пора ли запускать мониторинг для этого пользователя
                should_run = self._should_run_monitoring(settings)
                logger.info(f"🎯 SCHEDULER: Should run monitoring for user {user_id}: {should_run}")
                
                if should_run:
                    logger.info(f"🚀 SCHEDULER: Running monitoring for user {user_id}")
                    
                    # Запускаем мониторинг
                    await self._run_monitoring_for_user(user_id, settings)
                else:
                    logger.info(f"⏰ SCHEDULER: Skipping monitoring for user {user_id} - too early")
                    
        except Exception as e:
            logger.error(f"❌ SCHEDULER: Error in scheduled monitoring: {e}")
            import traceback
            logger.error(f"❌ SCHEDULER: Traceback: {traceback.format_exc()}")
    
    async def _get_active_monitoring_users(self) -> list:
        """Получить всех пользователей с активным мониторингом"""
        try:
            logger.info("📊 SCHEDULER: Querying database for active monitoring users")
            result = supabase_client.table('monitoring_settings').select('*').eq('is_active', True).execute()
            
            users = result.data or []
            logger.info(f"📊 SCHEDULER: Retrieved {len(users)} active monitoring users from database")
            
            for user in users:
                chats_count = len(user.get('monitored_chats', []))
                interval = user.get('check_interval_minutes', 'N/A')
                logger.info(f"👤 SCHEDULER: User {user['user_id']} - chats: {chats_count}, interval: {interval}min")
            
            return users
            
        except Exception as e:
            logger.error(f"❌ SCHEDULER: Error getting active monitoring users: {e}")
            return []
    
    def _should_run_monitoring(self, settings: dict) -> bool:
        """Проверить, нужно ли запускать мониторинг для пользователя"""
        try:
            last_check = settings.get('last_monitoring_check')
            interval_minutes = settings.get('check_interval_minutes', 5)
            
            logger.info(f"⏰ SCHEDULER: Checking interval - last_check: {last_check}, interval: {interval_minutes}min")
            
            if not last_check:
                logger.info("⏰ SCHEDULER: No last check time, running monitoring")
                return True
            
            # Обрабатываем время с учетом timezone
            try:
                # Парсим время из БД (может быть с timezone)
                if isinstance(last_check, str):
                    # Убираем Z и заменяем на +00:00 если есть
                    time_str = last_check.replace('Z', '+00:00')
                    last_check_time = datetime.fromisoformat(time_str)
                else:
                    last_check_time = last_check
                
                # Приводим к UTC если есть timezone info
                if last_check_time.tzinfo is not None:
                    last_check_utc = last_check_time.astimezone(timezone.utc)
                else:
                    # Если timezone нет, считаем что это UTC
                    last_check_utc = last_check_time.replace(tzinfo=timezone.utc)
                
                # Текущее время в UTC
                now_utc = datetime.now(timezone.utc)
                
                # Вычисляем разницу в минутах
                time_diff_minutes = (now_utc - last_check_utc).total_seconds() / 60
                
                logger.info(f"⏰ SCHEDULER: Time difference: {time_diff_minutes:.1f} minutes (need {interval_minutes})")
                
                if time_diff_minutes >= interval_minutes:
                    logger.info("✅ SCHEDULER: Interval elapsed, running monitoring")
                    return True
                else:
                    logger.info(f"⏳ SCHEDULER: Too early, need to wait {interval_minutes - time_diff_minutes:.1f} more minutes")
                    return False
                    
            except Exception as time_error:
                logger.warning(f"⚠️ SCHEDULER: Error parsing time, running monitoring anyway: {time_error}")
                return True
            
        except Exception as e:
            logger.error(f"❌ SCHEDULER: Error checking if should run monitoring: {e}")
            # При ошибке все равно запускаем мониторинг
            return True
    
    async def _run_monitoring_for_user(self, user_id: int, settings: dict):
        """Запустить мониторинг для конкретного пользователя"""
        try:
            logger.info(f"🚀 SCHEDULER: Starting monitoring execution for user {user_id}")
            
            # Обновляем время последней проверки в начале
            await self._update_last_check_time(user_id)
            
            # Получаем шаблоны продуктов
            templates = await self._get_user_templates(user_id)
            if not templates:
                logger.warning(f"❌ SCHEDULER: No active product templates found for user {user_id}")
                return
            
            logger.info(f"📝 SCHEDULER: Found {len(templates)} active templates for user {user_id}")
            
            # Получаем чаты для мониторинга
            monitored_chats = settings.get('monitored_chats', [])
            if not monitored_chats:
                logger.warning(f"❌ SCHEDULER: No monitored chats configured for user {user_id}")
                return
            
            logger.info(f"💬 SCHEDULER: Monitoring {len(monitored_chats)} chats for user {user_id}")
            
            # Запускаем поиск и анализ
            await self.monitoring_service._search_and_analyze(user_id, settings)
            
            logger.info(f"✅ SCHEDULER: Monitoring execution completed for user {user_id}")
            
        except Exception as e:
            logger.error(f"❌ SCHEDULER: Error running monitoring for user {user_id}: {e}")
    
    async def _update_last_check_time(self, user_id: int):
        """Обновить время последней проверки"""
        try:
            current_time = datetime.now(timezone.utc).isoformat()
            
            supabase_client.table('monitoring_settings').update({
                'last_monitoring_check': current_time
            }).eq('user_id', user_id).execute()
            
            logger.info(f"🕐 SCHEDULER: Updated last check time for user {user_id} to {current_time}")
            
        except Exception as e:
            logger.error(f"❌ SCHEDULER: Error updating last check time for user {user_id}: {e}")
    
    async def _get_user_templates(self, user_id: int) -> list:
        """Получить активные шаблоны пользователя"""
        try:
            result = supabase_client.table('product_templates').select('*').eq('user_id', user_id).eq('is_active', True).execute()
            
            templates = result.data or []
            logger.info(f"📝 SCHEDULER: Retrieved {len(templates)} active templates for user {user_id}")
            return templates
            
        except Exception as e:
            logger.error(f"❌ SCHEDULER: Error getting user templates for user {user_id}: {e}")
            return []

    @property
    def scheduler(self):
        """Совместимость с health check - эмулируем APScheduler"""
        class FakeScheduler:
            def __init__(self, running):
                self.running = running
        
        return FakeScheduler(self.running)

# Глобальный экземпляр планировщика
scheduler_service = SchedulerService()