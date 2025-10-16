"""
SQLAlchemy ORM модели для базы данных.
"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    Date,
    ForeignKey,
    UniqueConstraint,
)
from datetime import date
from sqlalchemy.dialects.postgresql import UUID  # Используем UUID для совместимости
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
import uuid


# Используем DeclarativeBase для определения моделей
class Base(DeclarativeBase):
    pass


# --- Справочники ---


class ScheduleType(Base):
    """
    Справочник типов расписания для привычек.
    """

    __tablename__ = "ScheduleType"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(
        String(50), nullable=False, unique=True
    )  # daily, weekly, custom

    # Связи
    # habits = relationship("Habit", back_populates="schedule_type") # Опционально, если нужно использовать relationship


class RewardType(Base):
    """
    Справочник типов наград.
    """

    __tablename__ = "RewardType"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(
        String(50), nullable=False, unique=True
    )  # badge, level, challenge

    # Связи
    # rewards = relationship("Reward", back_populates="reward_type")
    # challenges = relationship("Challenge", back_populates="reward_type")


class FriendStatus(Base):
    """
    Справочник статусов дружбы.
    """

    __tablename__ = "FriendStatus"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(
        String(50), nullable=False, unique=True
    )  # pending, accepted, rejected

    # Связи
    # friends = relationship("Friend", back_populates="status")


# --- Основные сущности ---


class User(Base):
    """
    Модель пользователя.
    """

    __tablename__ = "User"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    telegram_id: Mapped[int] = mapped_column(
        Integer, unique=True, nullable=False
    )  # Telegram ID как BIGINT
    username: Mapped[str | None] = mapped_column(String(100))
    first_name: Mapped[str | None] = mapped_column(String(100))
    last_name: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[DateTime | None] = mapped_column(DateTime)
    level: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    points: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    current_streak: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    longest_streak: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    timezone: Mapped[str | None] = mapped_column(String(50), default="Europe/Moscow")  # Часовой пояс пользователя

    # Связи
    # habits = relationship("Habit", back_populates="user", cascade="all, delete-orphan")
    # habit_completions = relationship("HabitCompletion", back_populates="user", cascade="all, delete-orphan")
    # rewards = relationship("Reward", back_populates="user", cascade="all, delete-orphan")
    # friend_requests_sent = relationship("Friend", foreign_keys="Friend.user_id", back_populates="user", cascade="all, delete-orphan")
    # friend_requests_received = relationship("Friend", foreign_keys="Friend.friend_id", back_populates="friend", cascade="all, delete-orphan")
    # challenge_participations = relationship("ChallengeParticipant", back_populates="user", cascade="all, delete-orphan")
    # notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")


class Habit(Base):
    """
    Модель привычки.
    """

    __tablename__ = "Habit"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("User.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500))
    schedule_type_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ScheduleType.id"), nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    color: Mapped[str | None] = mapped_column(String(7))  # HEX цвет, например #FF5733
    emoji: Mapped[str | None] = mapped_column(String(10))
    base_points: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    created_at: Mapped[DateTime | None] = mapped_column(DateTime)
    # Поля для custom расписания
    custom_schedule_days: Mapped[str | None] = mapped_column(String(50))  # JSON строка с днями недели
    custom_schedule_time: Mapped[str | None] = mapped_column(String(10))  # Время в формате HH:MM
    custom_schedule_frequency: Mapped[int] = mapped_column(Integer, default=1, nullable=False)  # Частота (каждый N день)
    timezone: Mapped[str | None] = mapped_column(String(50), default="Europe/Moscow")  # Часовой пояс пользователя

    # Связи
    # user = relationship("User", back_populates="habits")
    # schedule_type = relationship("ScheduleType", back_populates="habits")
    # completions = relationship("HabitCompletion", back_populates="habit", cascade="all, delete-orphan")
    # notifications = relationship("Notification", back_populates="habit", cascade="all, delete-orphan")


class HabitCompletion(Base):
    """
    Модель отметки выполнения привычки.
    """

    __tablename__ = "HabitCompletion"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    habit_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("Habit.id"), nullable=False
    )
    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("User.id"), nullable=False
    )
    completion_date: Mapped[date] = mapped_column(
        Date, nullable=False
    )  # Дата выполнения
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    bonus_point: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    streak_increment: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Уникальность: одна привычка не может быть отмечена дважды в один день
    __table_args__ = (
        UniqueConstraint("habit_id", "completion_date", name="_habit_date_uc"),
    )


class Reward(Base):
    """
    Модель награды, полученной пользователем.
    """

    __tablename__ = "Reward"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("User.id"), nullable=False
    )
    reward_type_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("RewardType.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500))
    awarded_at: Mapped[DateTime | None] = mapped_column(DateTime)

    # Связи
    # user = relationship("User", back_populates="rewards")
    # reward_type = relationship("RewardType", back_populates="rewards")


class Friend(Base):
    """
    Модель дружбы/запроса в друзья.
    """

    __tablename__ = "Friend"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("User.id"), nullable=False
    )  # Кто отправил запрос
    friend_id: Mapped[UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("User.id")
    )  # Кого добавили (NULL, если запрос не принят)
    friend_status_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("FriendStatus.id"), nullable=False
    )
    created_at: Mapped[DateTime | None] = mapped_column(DateTime)

    # Связи
    # user = relationship("User", foreign_keys=[user_id], back_populates="friend_requests_sent")
    # friend = relationship("User", foreign_keys=[friend_id], back_populates="friend_requests_received")
    # status = relationship("FriendStatus", back_populates="friends")


class Challenge(Base):
    """
    Модель челленджа.
    """

    __tablename__ = "Challenge"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500))
    start_date: Mapped[Date | None] = mapped_column(Date)
    end_date: Mapped[Date | None] = mapped_column(Date)
    points_reward: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    badge_reward: Mapped[str | None] = mapped_column(String(200))  # Название бейджа
    challenge_type: Mapped[str | None] = mapped_column(
        String(50)
    )  # daily, weekly, special

    # Связи
    # participants = relationship("ChallengeParticipant", back_populates="challenge", cascade="all, delete-orphan")
    # reward_type = relationship("RewardType", back_populates="challenges") # Связь с типом награды (например, 'challenge')


class ChallengeParticipant(Base):
    """
    Модель участника челленджа.
    """

    __tablename__ = "ChallengeParticipant"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    challenge_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("Challenge.id"), nullable=False
    )
    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("User.id"), nullable=False
    )
    progress: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    completed: Mapped[bool] = mapped_column(Boolean, default=False)

    # Связи
    # challenge = relationship("Challenge", back_populates="participants")
    # user = relationship("User", back_populates="challenge_participations")


class Notification(Base):
    """
    Модель уведомления.
    """

    __tablename__ = "Notification"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("User.id"), nullable=False
    )
    habit_id: Mapped[UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("Habit.id")
    )  # Может быть NULL
    challenge_id: Mapped[UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("Challenge.id")
    )  # Может быть NULL
    notification_time: Mapped[DateTime | None] = mapped_column(DateTime)
    is_sent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    message: Mapped[str | None] = mapped_column(String(500))

    # Связи
    # user = relationship("User", back_populates="notifications")
    # habit = relationship("Habit", back_populates="notifications")
    # challenge = relationship("Challenge", back_populates="participants") # Связь с Challenge, а не с ChallengeParticipant
