"""
Сервисы для работы с наградами и очками.
"""

from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.database import User, Reward, RewardType
from datetime import datetime


async def award_points_and_rewards(
    db: AsyncSession, user_telegram_id: int, points_to_add: int, current_streak: int = 0
):
    """
    Начисляет очки пользователю и проверяет, нужно ли выдать награды (бейджи, уровень).
    """
    # Найти пользователя по telegram_id
    result = await db.execute(select(User).where(User.telegram_id == user_telegram_id))
    user = result.scalar_one_or_none()
    if not user:
        raise ValueError(f"Пользователь с telegram_id {user_telegram_id} не найден.")

    # Получаем текущие значения как обычные Python объекты
    current_points = user.points
    current_level = user.level

    # Обновить очки
    new_points = current_points + points_to_add
    user.points = new_points

    # Проверить и обновить уровень (простая логика: 100 очков = 1 уровень)
    new_level = (new_points // 100) + 1  # Уровень минимум 1
    level_up = new_level > current_level

    if level_up:
        user.level = new_level
        # Выдать награду за повышение уровня
        level_reward_type_result = await db.execute(
            select(RewardType.id).where(RewardType.name == "level")
        )
        level_reward_type_id = level_reward_type_result.scalar_one_or_none()
        if level_reward_type_id:
            level_reward = Reward(
                user_id=user.id,
                reward_type_id=level_reward_type_id,
                name=f"Уровень {new_level}",
                description=f"Достигнут уровень {new_level}",
                awarded_at=datetime.utcnow(),
            )
            db.add(level_reward)

    # Проверить и выдать бейджи за серию (пример: 7, 30, 100 дней)
    badge_name: Optional[str] = None
    badge_desc: Optional[str] = None

    if current_streak >= 100:
        badge_name = "Сотня подряд"
        badge_desc = "Выполнили привычку 100 дней подряд!"
    elif current_streak >= 30:
        badge_name = "Месяц подряд"
        badge_desc = "Выполнили привычку 30 дней подряд!"
    elif current_streak >= 7:
        badge_name = "Неделя подряд"
        badge_desc = "Выполнили привычку 7 дней подряд!"

    if badge_name and badge_desc:
        badge_reward_type_result = await db.execute(
            select(RewardType.id).where(RewardType.name == "badge")
        )
        badge_reward_type_id = badge_reward_type_result.scalar_one_or_none()
        if badge_reward_type_id:
            # Проверим, не выдавался ли уже такой бейдж
            existing_badge_result = await db.execute(
                select(Reward).where(
                    Reward.user_id == user.id,
                    Reward.reward_type_id == badge_reward_type_id,
                    Reward.name == badge_name,
                )
            )
            existing_badge = existing_badge_result.scalar_one_or_none()

            if not existing_badge:
                badge_reward = Reward(
                    user_id=user.id,
                    reward_type_id=badge_reward_type_id,
                    name=badge_name,
                    description=badge_desc,
                    awarded_at=datetime.utcnow(),
                )
                db.add(badge_reward)

    await db.commit()


async def get_user_rewards(db: AsyncSession, user_telegram_id: int) -> List[Reward]:
    """
    Возвращает список наград пользователя по его telegram_id.
    """
    result = await db.execute(
        select(Reward)
        .join(User, Reward.user_id == User.id)
        .where(User.telegram_id == user_telegram_id)
    )
    rewards = result.scalars().all()
    return list(rewards)  # Явно преобразуем в список


async def get_user_level_info(db: AsyncSession, user_telegram_id: int):
    """
    Возвращает информацию об уровне пользователя.
    """
    result = await db.execute(
        select(User.level, User.points).where(User.telegram_id == user_telegram_id)
    )
    user_info = result.first()
    if user_info:
        level, points = user_info
        points_for_next_level = ((level) * 100) - points
        return {
            "level": level,
            "points": points,
            "points_for_next_level": points_for_next_level,
        }
    return None
