"""
Pydantic схемы для валидации данных API.
"""

from pydantic import BaseModel, Field
from datetime import datetime, date
from typing import Optional, List
from uuid import UUID


# --- Базовая схема ---
class BaseSchema(BaseModel):
    """
    Базовая схема, от которой наследуются все остальные.
    """

    class Config:
        from_attributes = True  # Позволяет читать данные из ORM моделей


# --- Схемы для справочников ---


class ScheduleTypeBase(BaseSchema):
    name: str = Field(
        ..., max_length=50, description="Название типа расписания (e.g., daily, weekly)"
    )


class ScheduleTypeCreate(ScheduleTypeBase):
    pass


class ScheduleType(ScheduleTypeBase):
    id: UUID
    # habits: List['Habit'] = [] # Опционально, если нужно возвращать связанные данные


class RewardTypeBase(BaseSchema):
    name: str = Field(
        ..., max_length=50, description="Название типа награды (e.g., badge, level)"
    )


class RewardTypeCreate(RewardTypeBase):
    pass


class RewardType(RewardTypeBase):
    id: UUID
    # rewards: List['Reward'] = [] # Опционально


class FriendStatusBase(BaseSchema):
    name: str = Field(
        ...,
        max_length=50,
        description="Название статуса дружбы (e.g., pending, accepted)",
    )


class FriendStatusCreate(FriendStatusBase):
    pass


class FriendStatus(FriendStatusBase):
    id: UUID
    # friends: List['Friend'] = [] # Опционально


# --- Схемы для основных сущностей ---


class UserBase(BaseSchema):
    telegram_id: int = Field(..., description="Telegram ID пользователя")
    username: Optional[str] = Field(None, max_length=100)
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)


class UserCreate(UserBase):
    # Поля, которые обязательны при создании
    pass


class UserUpdate(BaseSchema):
    # Поля, которые можно обновить
    username: Optional[str] = Field(None, max_length=100)
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)


class User(UserBase):
    id: UUID
    created_at: Optional[datetime]
    level: int = 1
    points: int = 0
    current_streak: int = 0
    longest_streak: int = 0
    # habits: List['Habit'] = []
    # rewards: List['Reward'] = []
    # friend_requests_sent: List['Friend'] = []
    # friend_requests_received: List['Friend'] = []
    # challenge_participations: List['ChallengeParticipant'] = []


class HabitBase(BaseSchema):
    name: str = Field(..., max_length=200, description="Название привычки")
    description: Optional[str] = Field(None, max_length=500)
    is_active: bool = True
    color: Optional[str] = Field(
        None, max_length=7, pattern=r"^#[0-9A-Fa-f]{6}$"
    )  # HEX цвет
    emoji: Optional[str] = Field(None, max_length=10)
    base_points: int = Field(10, ge=0, description="Базовые очки за выполнение")
    # Поля для custom расписания
    custom_schedule_days: Optional[str] = Field(None, max_length=50, description="Дни недели для custom расписания (JSON)")
    custom_schedule_time: Optional[str] = Field(None, max_length=10, description="Время напоминания (HH:MM)")
    custom_schedule_frequency: int = Field(1, ge=1, description="Частота выполнения (каждый N день)")


class HabitCreate(HabitBase):
    user_id: UUID
    schedule_type_id: UUID


class HabitUpdate(BaseSchema):
    name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None
    color: Optional[str] = Field(None, max_length=7, pattern=r"^#[0-9A-Fa-f]{6}$")
    emoji: Optional[str] = Field(None, max_length=10)
    base_points: Optional[int] = Field(None, ge=0)


class Habit(HabitBase):
    id: UUID
    user_id: UUID
    schedule_type_id: UUID
    created_at: Optional[datetime]
    user: Optional[User] = (
        None  # Опционально, если нужно возвращать данные пользователя
    )
    schedule_type: Optional[ScheduleType] = (
        None  # Опционально, если нужно возвращать тип расписания
    )


class HabitCompletionBase(BaseSchema):
    habit_id: UUID
    user_id: UUID
    completion_date: date
    is_completed: bool = False
    bonus_point: int = 0
    streak_increment: int = 0


class HabitCompletionCreate(HabitCompletionBase):
    pass


class HabitCompletionUpdate(BaseSchema):
    is_completed: Optional[bool] = None
    bonus_point: Optional[int] = Field(None, ge=0)
    streak_increment: Optional[int] = Field(None, ge=0)


class HabitCompletion(HabitCompletionBase):
    id: UUID
    habit: Optional[Habit] = None  # Опционально
    user: Optional[User] = None  # Опционально


class RewardBase(BaseSchema):
    user_id: UUID
    reward_type_id: UUID
    name: str = Field(..., max_length=200)
    description: Optional[str] = Field(None, max_length=500)


class RewardCreate(RewardBase):
    pass


class Reward(RewardBase):
    id: UUID
    awarded_at: Optional[datetime]
    user: Optional[User] = None  # Опционально
    reward_type: Optional[RewardType] = None  # Опционально


class FriendBase(BaseSchema):
    user_id: UUID
    friend_id: Optional[UUID] = None  # Может быть NULL до подтверждения
    friend_status_id: UUID


class FriendCreate(FriendBase):
    friend_telegram_id: int = Field(
        ..., description="Telegram ID друга, которого хотим добавить"
    )  # Поле для API, не входит в таблицу


class FriendUpdate(BaseSchema):
    friend_id: UUID  # При подтверждении запроса
    friend_status_id: UUID


class Friend(FriendBase):
    id: UUID
    created_at: Optional[datetime]
    user: Optional[User] = None  # Опционально
    friend: Optional[User] = None  # Опционально
    status: Optional[FriendStatus] = None  # Опционально


class ChallengeBase(BaseSchema):
    name: str = Field(..., max_length=200)
    description: Optional[str] = Field(None, max_length=500)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    points_reward: int = 0
    badge_reward: Optional[str] = Field(None, max_length=200)
    challenge_type: Optional[str] = Field(None, max_length=50)


class ChallengeCreate(ChallengeBase):
    pass


class ChallengeUpdate(BaseSchema):
    name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = Field(None, max_length=500)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    points_reward: Optional[int] = Field(None, ge=0)
    badge_reward: Optional[str] = Field(None, max_length=200)
    challenge_type: Optional[str] = Field(None, max_length=50)


class Challenge(ChallengeBase):
    id: UUID
    # participants: List['ChallengeParticipant'] = [] # Опционально


class ChallengeParticipantBase(BaseSchema):
    challenge_id: UUID
    user_id: UUID
    progress: int = 0
    completed: bool = False


class ChallengeParticipantCreate(ChallengeParticipantBase):
    pass


class ChallengeParticipantUpdate(BaseSchema):
    progress: Optional[int] = Field(None, ge=0)
    completed: Optional[bool] = None


class ChallengeParticipant(ChallengeParticipantBase):
    id: UUID
    challenge: Optional[Challenge] = None  # Опционально
    user: Optional[User] = None  # Опционально


class NotificationBase(BaseSchema):
    user_id: UUID
    habit_id: Optional[UUID] = None
    challenge_id: Optional[UUID] = None
    notification_time: Optional[datetime] = None
    is_sent: bool = False
    message: Optional[str] = Field(None, max_length=500)


class NotificationCreate(NotificationBase):
    pass


class NotificationUpdate(BaseSchema):
    is_sent: Optional[bool] = None
    message: Optional[str] = Field(None, max_length=500)


class Notification(NotificationBase):
    id: UUID
    user: Optional[User] = None  # Опционально
    habit: Optional[Habit] = None  # Опционально
    # challenge: Optional[Challenge] = None # Опционально
