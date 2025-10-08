"""
Сервисы для работы с привычками.
"""

from typing import List, Optional, Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.models.database import Habit, HabitCompletion, User
from datetime import date


async def create_habit(
    db: AsyncSession,
    telegram_id: int,
    name: str,
    description: str = "",
    schedule_type_id: str = "daily_uuid",  # Заглушка, нужно заменить на реальный UUID
) -> Habit:
    """
    Создаёт новую привычку для пользователя.
    """
    # Найти пользователя по telegram_id
    result = await db.execute(select(User.id).where(User.telegram_id == telegram_id))
    user_db_id = result.scalar_one_or_none()
    if not user_db_id:
        raise ValueError(f"Пользователь с telegram_id {telegram_id} не найден.")

    habit = Habit(
        user_id=user_db_id,
        name=name,
        description=description,
        schedule_type_id=schedule_type_id,  # Используем заглушку
    )
    db.add(habit)
    await db.commit()
    await db.refresh(habit)
    return habit


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
    habit_id: str,
    user_id: str,
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
    # Пока возвращает заглушку, требует реализации
    return {"message": f"Статистика для пользователя {telegram_id}"}
