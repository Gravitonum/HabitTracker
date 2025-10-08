"""
Сервисы для работы с пользователями.
"""

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.database import User
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


async def get_or_create_user(
    db: AsyncSession,
    telegram_id: int,
    username: Optional[str] = None,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
) -> User:
    """
    Получает пользователя по telegram_id или создает нового, если не найден.
    """
    # Сначала пытаемся найти существующего пользователя
    result = await db.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalar_one_or_none()
    
    if user:
        # Обновляем информацию о пользователе, если она изменилась
        updated = False
        if user.username != username:
            user.username = username
            updated = True
        if user.first_name != first_name:
            user.first_name = first_name
            updated = True
        if user.last_name != last_name:
            user.last_name = last_name
            updated = True
        
        if updated:
            await db.commit()
            await db.refresh(user)
            logger.info(f"Обновлена информация о пользователе {telegram_id}")
        
        return user
    
    # Создаем нового пользователя
    user = User(
        telegram_id=telegram_id,
        username=username,
        first_name=first_name,
        last_name=last_name,
        created_at=datetime.utcnow(),
        level=1,
        points=0,
        current_streak=0,
        longest_streak=0,
    )
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    logger.info(f"Создан новый пользователь: {telegram_id} ({first_name} {last_name})")
    return user


async def get_user_by_telegram_id(db: AsyncSession, telegram_id: int) -> Optional[User]:
    """
    Получает пользователя по telegram_id.
    """
    result = await db.execute(select(User).where(User.telegram_id == telegram_id))
    return result.scalar_one_or_none()


async def update_user_points(db: AsyncSession, user_id, points: int) -> User:
    """
    Обновляет очки пользователя.
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one()
    
    user.points += points
    await db.commit()
    await db.refresh(user)
    
    return user


async def update_user_streak(db: AsyncSession, user_id, current_streak: int, longest_streak: int) -> User:
    """
    Обновляет серию пользователя.
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one()
    
    user.current_streak = current_streak
    user.longest_streak = max(user.longest_streak, longest_streak)
    
    await db.commit()
    await db.refresh(user)
    
    return user
