"""
Сервисы для работы с привычками.
"""

from typing import List, Optional, Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.models.database import Habit, HabitCompletion, User, ScheduleType
from datetime import date


async def create_habit(
    db: AsyncSession,
    telegram_id: int,
    name: str,
    description: str = "",
    schedule_type: str = "daily",
    custom_schedule_days: str = None,
    custom_schedule_time: str = None,
    custom_schedule_frequency: int = 1,
    timezone: str = "Europe/Moscow",
) -> Habit:
    """
    Создаёт новую привычку для пользователя.
    """
    # Найти пользователя по telegram_id
    result = await db.execute(select(User.id).where(User.telegram_id == telegram_id))
    user_db_id = result.scalar_one_or_none()
    if not user_db_id:
        raise ValueError(f"Пользователь с telegram_id {telegram_id} не найден.")

    # Получить UUID для указанного типа расписания
    schedule_result = await db.execute(select(ScheduleType.id).where(ScheduleType.name == schedule_type))
    schedule_type_id = schedule_result.scalar_one_or_none()
    if not schedule_type_id:
        raise ValueError(f"Тип расписания '{schedule_type}' не найден в справочнике.")

    habit = Habit(
        user_id=user_db_id,
        name=name,
        description=description,
        schedule_type_id=schedule_type_id,
        custom_schedule_days=custom_schedule_days,
        custom_schedule_time=custom_schedule_time,
        custom_schedule_frequency=custom_schedule_frequency,
        timezone=timezone,
    )
    db.add(habit)
    await db.commit()
    await db.refresh(habit)
    return habit


async def get_available_schedule_types(db: AsyncSession) -> Sequence[ScheduleType]:
    """
    Возвращает список доступных типов расписания.
    """
    result = await db.execute(select(ScheduleType))
    schedule_types = result.scalars().all()
    return schedule_types


async def get_user_habits(db: AsyncSession, telegram_id: int) -> Sequence[Habit]:
    """
    Возвращает список привычек пользователя по его telegram_id.
    """
    result = await db.execute(
        select(Habit)
        .join(User, Habit.user_id == User.id)
        .where(User.telegram_id == telegram_id)
        .where(Habit.is_active == True)  # Только активные
    )
    habits = result.scalars().all()
    return habits


async def mark_habit_completed(
    db: AsyncSession,
    habit_id,
    user_id,
    completion_date: date,
    streak_increment: int = 0,
) -> HabitCompletion:
    """
    Отмечает привычку как выполненную на указанную дату.
    """
    # Проверяем, существует ли уже отметка на эту дату
    existing_completion = await db.execute(
        select(HabitCompletion).where(
            and_(
                HabitCompletion.habit_id == habit_id,
                HabitCompletion.completion_date == completion_date,
            )
        )
    )
    existing = existing_completion.scalar_one_or_none()

    if existing:
        # Обновляем существующую отметку
        existing.is_completed = True
        existing.streak_increment = streak_increment
        await db.commit()
        await db.refresh(existing)
        return existing
    else:
        # Создаём новую отметку
        completion = HabitCompletion(
            habit_id=habit_id,
            user_id=user_id,
            completion_date=completion_date,
            is_completed=True,
            streak_increment=streak_increment,
        )
        db.add(completion)
        await db.commit()
        await db.refresh(completion)
        return completion


async def get_habit_by_id(db: AsyncSession, habit_id: str) -> Optional[Habit]:
    """
    Возвращает привычку по её ID.
    """
    result = await db.execute(select(Habit).where(Habit.id == habit_id))
    habit = result.scalar_one_or_none()
    return habit


async def get_all_completions_for_habit(
    db: AsyncSession, habit_id: str
) -> Sequence[HabitCompletion]:
    """
    Возвращает все отметки выполнения для конкретной привычки.
    """
    result = await db.execute(
        select(HabitCompletion)
        .where(HabitCompletion.habit_id == habit_id)
        .order_by(HabitCompletion.completion_date)
    )
    completions = result.scalars().all()
    return completions


async def get_user_statistics(db: AsyncSession, telegram_id: int):
    """
    Возвращает статистику по привычкам пользователя.
    """
    from datetime import date, timedelta
    from sqlalchemy import func, and_
    
    # Получаем пользователя
    user_result = await db.execute(select(User).where(User.telegram_id == telegram_id))
    user = user_result.scalar_one_or_none()
    if not user:
        return {"error": "Пользователь не найден"}
    
    # Получаем все привычки пользователя
    habits_result = await db.execute(
        select(Habit)
        .where(Habit.user_id == user.id)
        .where(Habit.is_active == True)
    )
    habits = habits_result.scalars().all()
    
    if not habits:
        return {
            "habits": [],
            "total_habits": 0,
            "completed_today": 0,
            "total_completions": 0,
            "average_completion_rate": 0
        }
    
    # Получаем статистику по каждой привычке
    habit_stats = []
    total_completions = 0
    completed_today = 0
    
    for habit in habits:
        # Подсчитываем общее количество выполнений
        completions_result = await db.execute(
            select(func.count(HabitCompletion.id))
            .where(HabitCompletion.habit_id == habit.id)
            .where(HabitCompletion.is_completed == True)
        )
        total_completions_count = completions_result.scalar() or 0
        
        # Подсчитываем выполнение сегодня
        today_result = await db.execute(
            select(HabitCompletion)
            .where(HabitCompletion.habit_id == habit.id)
            .where(HabitCompletion.completion_date == date.today())
            .where(HabitCompletion.is_completed == True)
        )
        is_completed_today = today_result.scalar_one_or_none() is not None
        
        if is_completed_today:
            completed_today += 1
        
        # Подсчитываем серию (последние последовательные дни)
        current_streak = await calculate_current_streak(db, habit.id)
        
        # Подсчитываем выполнение за последние 7 дней
        week_ago = date.today() - timedelta(days=7)
        week_completions_result = await db.execute(
            select(func.count(HabitCompletion.id))
            .where(HabitCompletion.habit_id == habit.id)
            .where(HabitCompletion.completion_date >= week_ago)
            .where(HabitCompletion.is_completed == True)
        )
        week_completions = week_completions_result.scalar() or 0
        
        habit_stats.append({
            "habit": habit,
            "total_completions": total_completions_count,
            "completed_today": is_completed_today,
            "current_streak": current_streak,
            "week_completions": week_completions,
            "completion_rate": (week_completions / 7) * 100 if week_completions > 0 else 0
        })
        
        total_completions += total_completions_count
    
    # Общий прогресс (процент привычек, выполненных сегодня)
    overall_progress = (completed_today / len(habits)) * 100 if habits else 0
    
    return {
        "habits": habit_stats,
        "total_habits": len(habits),
        "completed_today": completed_today,
        "total_completions": total_completions,
        "overall_progress": overall_progress
    }


async def calculate_current_streak(db: AsyncSession, habit_id) -> int:
    """
    Вычисляет текущую серию выполнения привычки.
    """
    from datetime import date, timedelta
    
    streak = 0
    current_date = date.today()
    
    while True:
        # Проверяем, была ли привычка выполнена в этот день
        result = await db.execute(
            select(HabitCompletion)
            .where(HabitCompletion.habit_id == habit_id)
            .where(HabitCompletion.completion_date == current_date)
            .where(HabitCompletion.is_completed == True)
        )
        
        if result.scalar_one_or_none():
            streak += 1
            current_date -= timedelta(days=1)
        else:
            break
    
    return streak


async def get_users_with_uncompleted_daily_habits(db: AsyncSession, target_date: date = None):
    """
    Возвращает пользователей с незавершенными привычками на указанную дату.
    Учитывает все типы привычек: daily, weekly, custom.
    """
    from app.utils.timezone_utils import is_habit_day_today, get_user_timezone
    from datetime import datetime
    
    if target_date is None:
        target_date = date.today()
    
    # Получаем всех пользователей с активными привычками
    result = await db.execute(
        select(User, Habit, ScheduleType)
        .join(Habit, User.id == Habit.user_id)
        .join(ScheduleType, Habit.schedule_type_id == ScheduleType.id)
        .where(Habit.is_active == True)
    )
    
    user_habits = result.all()
    
    # Группируем по пользователям
    users_with_habits = {}
    for user, habit, schedule_type in user_habits:
        if user.id not in users_with_habits:
            users_with_habits[user.id] = {
                'user': user,
                'habits': [],
                'uncompleted_habits': []
            }
        users_with_habits[user.id]['habits'].append((habit, schedule_type))
    
    # Проверяем, какие привычки не выполнены
    for user_id, data in users_with_habits.items():
        for habit, schedule_type in data['habits']:
            # Проверяем, должна ли выполняться привычка сегодня
            should_execute_today = False
            
            if schedule_type.name == "daily":
                # Ежедневные привычки выполняются каждый день
                should_execute_today = True
            elif schedule_type.name == "weekly":
                # Еженедельные привычки выполняются раз в неделю
                # Для простоты считаем, что они должны выполняться в понедельник
                should_execute_today = datetime.now(get_user_timezone(habit.timezone)).weekday() == 0
            elif schedule_type.name == "custom":
                # Custom привычки выполняются по расписанию
                if habit.custom_schedule_days:
                    should_execute_today = is_habit_day_today(habit.custom_schedule_days, habit.timezone)
                else:
                    # Если дни не указаны, считаем ежедневной
                    should_execute_today = True
            
            if should_execute_today:
                # Проверяем, была ли привычка выполнена в этот день
                completion_result = await db.execute(
                    select(HabitCompletion)
                    .where(HabitCompletion.habit_id == habit.id)
                    .where(HabitCompletion.completion_date == target_date)
                    .where(HabitCompletion.is_completed == True)
                )
                
                if not completion_result.scalar_one_or_none():
                    data['uncompleted_habits'].append(habit)
    
    # Возвращаем только пользователей с незавершенными привычками
    return [data for data in users_with_habits.values() if data['uncompleted_habits']]
