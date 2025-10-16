#!/usr/bin/env python3
"""
Скрипт для отладки привычек в Docker контейнере.
"""

import os
import sys
import asyncio
from pathlib import Path

# Добавляем путь к приложению
sys.path.append('/app')

from app.core.database import get_db_session
from app.models.database import User, Habit, ScheduleType
from sqlalchemy import select
from datetime import date


async def debug_habits():
    """Отладка привычек пользователя."""
    print("=== Отладка привычек ===")
    
    # Телеграм ID пользователя (замените на ваш)
    telegram_id = 187718933  # Замените на ваш ID
    
    try:
        async for db in get_db_session():
            # 1. Проверяем, есть ли пользователь в базе
            print(f"1. Поиск пользователя с telegram_id = {telegram_id}")
            user_result = await db.execute(
                select(User).where(User.telegram_id == telegram_id)
            )
            user_obj = user_result.scalar_one_or_none()
            
            if not user_obj:
                print("❌ Пользователь не найден в базе данных")
                return
            else:
                print(f"✅ Пользователь найден: {user_obj.first_name} (ID: {user_obj.id})")
            
            # 2. Проверяем все привычки пользователя
            print(f"\n2. Поиск всех привычек пользователя")
            all_habits_result = await db.execute(
                select(Habit, ScheduleType)
                .join(ScheduleType, Habit.schedule_type_id == ScheduleType.id)
                .where(Habit.user_id == user_obj.id)
            )
            all_habits = all_habits_result.all()
            print(f"Всего привычек: {len(all_habits)}")
            
            for habit, schedule_type in all_habits:
                print(f"  - {habit.name} (активна: {habit.is_active}, тип: {schedule_type.name})")
            
            # 3. Проверяем только активные привычки
            print(f"\n3. Поиск активных привычек")
            active_habits_result = await db.execute(
                select(Habit, ScheduleType)
                .join(ScheduleType, Habit.schedule_type_id == ScheduleType.id)
                .where(Habit.user_id == user_obj.id)
                .where(Habit.is_active == True)
            )
            active_habits = active_habits_result.all()
            print(f"Активных привычек: {len(active_habits)}")
            
            for habit, schedule_type in active_habits:
                print(f"  - {habit.name} (тип: {schedule_type.name})")
                if schedule_type.name == "custom":
                    print(f"    Custom расписание: {habit.custom_schedule_days} в {habit.custom_schedule_time}")
            
            # 4. Проверяем функцию get_users_with_uncompleted_daily_habits
            print(f"\n4. Тестирование get_users_with_uncompleted_daily_habits")
            from app.bot.services.habit_service import get_users_with_uncompleted_daily_habits
            
            users_to_notify = await get_users_with_uncompleted_daily_habits(db)
            print(f"Пользователей с незавершенными привычками: {len(users_to_notify)}")
            
            for user_data in users_to_notify:
                if user_data['user'].telegram_id == telegram_id:
                    print(f"✅ Найден пользователь {user_data['user'].first_name}")
                    print(f"Незавершенных привычек: {len(user_data['uncompleted_habits'])}")
                    for habit in user_data['uncompleted_habits']:
                        print(f"  - {habit.name}")
                    break
            else:
                print("❌ Пользователь не найден в списке для уведомлений")
            
            # 5. Проверяем завершения привычек за сегодня
            print(f"\n5. Проверка завершений за сегодня ({date.today()})")
            from app.models.database import HabitCompletion
            
            for habit, schedule_type in active_habits:
                completion_result = await db.execute(
                    select(HabitCompletion)
                    .where(HabitCompletion.habit_id == habit.id)
                    .where(HabitCompletion.completion_date == date.today())
                    .where(HabitCompletion.is_completed == True)
                )
                completion = completion_result.scalar_one_or_none()
                print(f"  - {habit.name}: {'✅ выполнена' if completion else '❌ не выполнена'}")
            
            break
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(debug_habits())
