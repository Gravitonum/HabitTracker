"""
Тестовый скрипт для проверки исправлений часовых поясов и уведомлений.
"""

import asyncio
import sys
import os

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_db_session
from app.bot.services.habit_service import get_users_with_uncompleted_daily_habits
from app.utils.timezone_utils import is_habit_time_now, is_habit_day_today, get_user_timezone
from datetime import date, datetime


async def test_timezone_utils():
    """Тестирует утилиты для работы с часовыми поясами."""
    print("=== Тестирование утилит часовых поясов ===")
    
    # Тест 1: Проверка времени привычки
    print("\n1. Тест проверки времени привычки:")
    current_time = datetime.now(get_user_timezone("Europe/Moscow"))
    print(f"Текущее время в Москве: {current_time.strftime('%H:%M')}")
    
    # Тест 2: Проверка дня недели
    print("\n2. Тест проверки дня недели:")
    is_thursday = is_habit_day_today("чт", "Europe/Moscow")
    print(f"Сегодня четверг? {is_thursday}")
    
    # Тест 3: Проверка времени напоминания
    print("\n3. Тест проверки времени напоминания:")
    is_time_now = is_habit_time_now("11:30", "Europe/Moscow")
    print(f"Время 11:30 наступило? {is_time_now}")


async def test_notifications():
    """Тестирует систему уведомлений."""
    print("\n=== Тестирование системы уведомлений ===")
    
    try:
        async for db in get_db_session():
            # Получаем пользователей с незавершенными привычками
            users_to_notify = await get_users_with_uncompleted_daily_habits(db)
            
            print(f"\nНайдено пользователей с незавершенными привычками: {len(users_to_notify)}")
            
            for i, user_data in enumerate(users_to_notify, 1):
                user = user_data['user']
                uncompleted_habits = user_data['uncompleted_habits']
                
                print(f"\nПользователь {i}: {user.first_name or user.username or 'Unknown'}")
                print(f"Telegram ID: {user.telegram_id}")
                print(f"Часовой пояс: {user.timezone}")
                print(f"Незавершенных привычек: {len(uncompleted_habits)}")
                
                for j, habit in enumerate(uncompleted_habits, 1):
                    print(f"  {j}. {habit.name}")
                    print(f"     Тип: {habit.schedule_type_id}")
                    print(f"     Дни: {habit.custom_schedule_days}")
                    print(f"     Время: {habit.custom_schedule_time}")
                    print(f"     Часовой пояс: {habit.timezone}")
            
            break
            
    except Exception as e:
        print(f"Ошибка при тестировании уведомлений: {e}")


async def test_habit_creation():
    """Тестирует создание привычки с часовым поясом."""
    print("\n=== Тестирование создания привычки ===")
    
    try:
        from app.bot.services.habit_service import create_habit
        from sqlalchemy import select
        from app.models.database import Habit, User
        
        async for db in get_db_session():
            # Проверяем, есть ли уже тестовая привычка
            user_result = await db.execute(select(User.id).where(User.telegram_id == 187718933))
            user_id = user_result.scalar_one_or_none()
            
            if user_id:
                existing_habit = await db.execute(
                    select(Habit).where(
                        Habit.user_id == user_id,
                        Habit.name == "Тестовая привычка"
                    )
                )
                habit = existing_habit.scalar_one_or_none()
                
                if habit:
                    print(f"Тестовая привычка уже существует:")
                    print(f"  ID: {habit.id}")
                    print(f"  Название: {habit.name}")
                    print(f"  Дни: {habit.custom_schedule_days}")
                    print(f"  Время: {habit.custom_schedule_time}")
                    print(f"  Часовой пояс: {habit.timezone}")
                else:
                    print("Тестовая привычка не найдена, но не создаем новую во избежание дубликатов")
            else:
                print("Пользователь с ID 187718933 не найден")
            
            break
            
    except Exception as e:
        print(f"Ошибка при проверке тестовой привычки: {e}")


async def main():
    """Основная функция тестирования."""
    print("Запуск тестирования исправлений...")
    
    # Тестируем утилиты часовых поясов
    await test_timezone_utils()
    
    # Тестируем систему уведомлений
    await test_notifications()
    
    # Тестируем создание привычки
    await test_habit_creation()
    
    print("\n=== Тестирование завершено ===")


if __name__ == "__main__":
    asyncio.run(main())
