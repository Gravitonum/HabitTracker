"""
Модуль для настройки подключения к базе данных с использованием SQLAlchemy и aiosqlite.
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool
from .config import settings

# Создаем асинхронный движок
# Для SQLite используем aiosqlite
engine = create_async_engine(
    settings.DATABASE_URL,
    # Параметры для SQLite
    connect_args={
        "check_same_thread": False,  # Необходимо для SQLite
    },
    # Пул подключений
    poolclass=StaticPool,  # Используем StaticPool для SQLite в тестовых целях
    echo=False,  # Установите True для логирования SQL-запросов
)

# Создаем асинхронный сессионный фабрику с использованием async_sessionmaker
AsyncSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


# Зависимость для получения сессии базы данных в FastAPI
async def get_db_session():
    """
    Асинхронная зависимость для получения сессии базы данных.
    """
    async with AsyncSessionLocal() as session:  # Создаем экземпляр сессии
        try:
            yield session
        finally:
            await session.close()
