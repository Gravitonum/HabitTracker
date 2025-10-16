"""
Модуль планировщика задач для отправки напоминаний и выполнения регулярных фоновых задач.
Использует APScheduler с асинхронным выполнением.
"""

import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from telegram.ext import Application
import logging

logger = logging.getLogger(__name__)


class HabitReminderScheduler:
    """
    Класс для управления планировщиком задач напоминаний.
    """

    def __init__(self, telegram_app: Application):
        self.scheduler = AsyncIOScheduler()
        self.telegram_app = telegram_app
        self.is_running = False

    async def start(self):
        """
        Запускает планировщик задач.
        """
        if not self.is_running:
            self.scheduler.start()
            self.is_running = True
            logger.info("Планировщик задач запущен.")

            # Проверка напоминаний каждую минуту для более точного контроля
            self.scheduler.add_job(
                self.send_daily_reminders,
                CronTrigger(minute="*"),  # Каждую минуту
                id="habit_reminder_check",
            )

            # Пример: Еженедельная проверка челленджей в понедельник в 9:00
            self.scheduler.add_job(
                self.check_weekly_challenges,
                CronTrigger(day_of_week="mon", hour=9, minute=0),
                id="weekly_challenge_check",
            )

    async def stop(self):
        """
        Останавливает планировщик задач.
        """
        if self.is_running:
            self.scheduler.shutdown()
            self.is_running = False
            logger.info("Планировщик задач остановлен.")

    async def send_daily_reminders(self):
        """
        Асинхронная задача для отправки ежедневных напоминаний пользователям.
        Учитывает индивидуальные настройки частоты напоминаний.
        """
        logger.info("Запуск задачи отправки ежедневных напоминаний.")
        
        try:
            from app.core.database import get_db_session
            from app.bot.services.habit_service import get_users_with_uncompleted_daily_habits
            from datetime import date, datetime
            from app.utils.timezone_utils import is_habit_time_now, get_user_timezone
            
            # Получаем пользователей с незавершенными привычками
            async for db in get_db_session():
                users_to_notify = await get_users_with_uncompleted_daily_habits(db)
                
                if not users_to_notify:
                    logger.info("Нет пользователей для отправки напоминаний.")
                    break
                
                logger.info(f"Найдено {len(users_to_notify)} пользователей с незавершенными привычками.")
                
                for user_data in users_to_notify:
                    user = user_data['user']
                    uncompleted_habits = user_data['uncompleted_habits']
                    
                    if not uncompleted_habits:
                        continue
                    
                    # Проверяем, нужно ли отправлять напоминание этому пользователю
                    if not self._should_send_reminder(user):
                        continue
                    
                    # Фильтруем привычки по времени напоминания
                    habits_to_remind = []
                    for habit in uncompleted_habits:
                        if habit.custom_schedule_time:
                            # Проверяем, наступило ли время для напоминания
                            if is_habit_time_now(habit.custom_schedule_time, habit.timezone):
                                habits_to_remind.append(habit)
                        else:
                            # Для привычек без времени добавляем в список
                            habits_to_remind.append(habit)
                    
                    if not habits_to_remind:
                        continue
                    
                    # Формируем сообщение с незавершенными привычками
                    habit_names = [habit.name for habit in habits_to_remind]
                    message = (
                        f"🔔 Напоминание о привычках\n\n"
                        f"Привет, {user.first_name or user.username or 'пользователь'}!\n"
                        f"Не забудьте выполнить свои привычки:\n\n"
                    )
                    
                    for i, habit_name in enumerate(habit_names, 1):
                        message += f"{i}. {habit_name}\n"
                    
                    message += f"\nИспользуйте /complete <номер> для отметки выполнения."
                    
                    try:
                        await self.telegram_app.bot.send_message(
                            chat_id=user.telegram_id,
                            text=message
                        )
                        logger.info(f"Напоминание отправлено пользователю {user.telegram_id}")
                        await asyncio.sleep(0.1)  # Небольшая задержка между сообщениями
                    except Exception as e:
                        logger.error(f"Ошибка при отправке напоминания пользователю {user.telegram_id}: {e}")
                
                break
                
        except Exception as e:
            logger.error(f"Ошибка в задаче отправки напоминаний: {e}")

    def _should_send_reminder(self, user):
        """
        Проверяет, нужно ли отправлять напоминание пользователю в данный момент.
        Учитывает индивидуальные настройки частоты напоминаний.
        """
        from datetime import datetime
        
        frequency = user.reminder_frequency or "0"
        now = datetime.now()
        
        # Если частота не задана или "0" - каждый час в начале часа
        if frequency == "0":
            return now.minute == 0
        
        # Если частота задана как cron-выражение (например, "*/10", "*/15", "*/30", "*/45")
        if frequency.startswith("*/"):
            try:
                interval = int(frequency[2:])  # Извлекаем число после "*/"
                return now.minute % interval == 0
            except ValueError:
                return False
        
        # Если частота "daily_start" - каждый день в начале дня (00:00)
        if frequency == "daily_start":
            return now.hour == 0 and now.minute == 0
        
        # Если частота "daily_end" - каждый день в конце дня (18:00)
        if frequency == "daily_end":
            return now.hour == 18 and now.minute == 0
        
        # По умолчанию - каждый час
        return now.minute == 0

    async def check_weekly_challenges(self):
        """
        Асинхронная задача для проверки и обновления статуса недельных челленджей.
        """
        logger.info("Запуск задачи проверки недельных челленджей.")
        # Логика проверки прогресса участников челленджей
        # и начисления наград
        # Пример:
        # await update_weekly_challenge_progress()
        # await award_challenge_rewards()

    # Метод для добавления пользовательской задачи (опционально)
    def add_job(self, func, trigger, id=None, **kwargs):
        """
        Добавляет новую задачу в планировщик.
        """
        self.scheduler.add_job(func, trigger, id=id, **kwargs)
        logger.info(f"Добавлена задача с ID: {id}")


# Глобальный экземпляр планировщика (можно заменить на DI при необходимости)
# scheduler_instance = None

# async def init_scheduler(telegram_app: Application):
#     """
#     Инициализирует и запускает планировщик.
#     """
#     global scheduler_instance
#     scheduler_instance = HabitReminderScheduler(telegram_app)
#     await scheduler_instance.start()
#     return scheduler_instance
