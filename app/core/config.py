"""
Модуль конфигурации приложения.
Содержит настройки, загружаемые из переменных окружения.
"""

import os
from dotenv import load_dotenv
from pathlib import Path

# Загружаем переменные окружения из файла .env (если он существует)
# Пробуем несколько возможных путей для .env файла
env_paths = [
    Path(".env"),
    Path("../.env"),
    Path("/app/.env"),
    Path("/app/../.env"),
    Path("/app/docker/.env"),
    Path("/app/docker/../.env")
]

env_loaded = False
for env_path in env_paths:
    if env_path.exists():
        load_dotenv(env_path)
        print(f"Loaded .env from: {env_path.absolute()}")
        env_loaded = True
        break

if not env_loaded:
    print("No .env file found, using environment variables only")
    # Попробуем загрузить .env из текущей директории без указания пути
    try:
        load_dotenv()
        print("Tried to load .env from current directory")
    except Exception as e:
        print(f"Failed to load .env: {e}")


class Settings:
    """
    Класс для хранения настроек приложения.
    """

    # Основные настройки
    PROJECT_NAME: str = "Habits Tracker Bot"
    PROJECT_VERSION: str = "0.1.0"

    # Настройки Telegram бота
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_WEBHOOK_URL: str = os.getenv("TELEGRAM_WEBHOOK_URL", "")

    # Настройки базы данных
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", "sqlite+aiosqlite:///./habits_tracker.db"
    )
    # Альтернативный путь для SQLite без aiosqlite: "sqlite:///./habits_tracker.db"

    # Настройки JWT (если понадобятся для API)
    SECRET_KEY: str = os.getenv(
        "SECRET_KEY", "your-default-secret-key-change-it-in-production"
    )
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
        os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
    )

    # Настройки логирования
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # Настройки геймификации
    POINTS_PER_HABIT_COMPLETION: int = int(
        os.getenv("POINTS_PER_HABIT_COMPLETION", "10")
    )
    STREAK_BONUS_MULTIPLIER: float = float(
        os.getenv("STREAK_BONUS_MULTIPLIER", "0.1")
    )  # 10% за каждый день подряд
    MAX_STREAK_DAYS: int = int(
        os.getenv("MAX_STREAK_DAYS", "365")
    )  # Максимальная длина серии для бонуса
    # ID администратора для получения уведомлений о ошибках
    ADMIN_ID: int = int(os.getenv("ADMIN_TELEGRAM_ID", "1234567890"))

# Экземпляр настроек для импорта
settings = Settings()
