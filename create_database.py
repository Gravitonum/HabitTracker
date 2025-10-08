import sqlite3
import uuid
from datetime import datetime


def create_database(db_path="habits_tracker.db"):
    """
    Создает файл базы данных SQLite с необходимой структурой таблиц и заполняет справочники.
    Соответствует текущей структуре моделей в app/models/database.py
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Включаем поддержку внешних ключей
    cursor.execute("PRAGMA foreign_keys = ON;")

    # Таблица справочника типов расписания
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS "ScheduleType" (
            "id" TEXT PRIMARY KEY,
            "name" TEXT NOT NULL UNIQUE
        );
    """
    )

    # Таблица справочника типов наград
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS "RewardType" (
            "id" TEXT PRIMARY KEY,
            "name" TEXT NOT NULL UNIQUE
        );
    """
    )

    # Таблица справочника статусов дружбы
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS "FriendStatus" (
            "id" TEXT PRIMARY KEY,
            "name" TEXT NOT NULL UNIQUE
        );
    """
    )

    # Таблица пользователей
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS "User" (
            "id" TEXT PRIMARY KEY,
            "telegram_id" INTEGER UNIQUE NOT NULL,
            "username" TEXT,
            "first_name" TEXT,
            "last_name" TEXT,
            "created_at" TEXT,
            "level" INTEGER NOT NULL DEFAULT 1,
            "points" INTEGER NOT NULL DEFAULT 0,
            "current_streak" INTEGER NOT NULL DEFAULT 0,
            "longest_streak" INTEGER NOT NULL DEFAULT 0
        );
    """
    )

    # Таблица привычек (обновлена с полями для custom расписания)
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS "Habit" (
            "id" TEXT PRIMARY KEY,
            "user_id" TEXT NOT NULL,
            "name" TEXT NOT NULL,
            "description" TEXT,
            "schedule_type_id" TEXT NOT NULL,
            "is_active" INTEGER NOT NULL DEFAULT 1,
            "color" TEXT,
            "emoji" TEXT,
            "base_points" INTEGER NOT NULL DEFAULT 10,
            "created_at" TEXT,
            "custom_schedule_days" TEXT,
            "custom_schedule_time" TEXT,
            "custom_schedule_frequency" INTEGER NOT NULL DEFAULT 1,
            FOREIGN KEY ("user_id") REFERENCES "User" ("id"),
            FOREIGN KEY ("schedule_type_id") REFERENCES "ScheduleType" ("id")
        );
    """
    )

    # Таблица отметок выполнения привычек
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS "HabitCompletion" (
            "id" TEXT PRIMARY KEY,
            "habit_id" TEXT NOT NULL,
            "user_id" TEXT NOT NULL,
            "completion_date" TEXT NOT NULL,
            "is_completed" INTEGER DEFAULT 0,
            "bonus_point" INTEGER NOT NULL DEFAULT 0,
            "streak_increment" INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY ("habit_id") REFERENCES "Habit" ("id"),
            FOREIGN KEY ("user_id") REFERENCES "User" ("id"),
            UNIQUE("habit_id", "completion_date")
        );
    """
    )

    # Таблица наград
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS "Reward" (
            "id" TEXT PRIMARY KEY,
            "user_id" TEXT NOT NULL,
            "reward_type_id" TEXT NOT NULL,
            "name" TEXT NOT NULL,
            "description" TEXT,
            "awarded_at" TEXT,
            FOREIGN KEY ("user_id") REFERENCES "User" ("id"),
            FOREIGN KEY ("reward_type_id") REFERENCES "RewardType" ("id")
        );
    """
    )

    # Таблица дружбы
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS "Friend" (
            "id" TEXT PRIMARY KEY,
            "user_id" TEXT NOT NULL,
            "friend_id" TEXT,
            "friend_status_id" TEXT NOT NULL,
            "created_at" TEXT,
            FOREIGN KEY ("user_id") REFERENCES "User" ("id"),
            FOREIGN KEY ("friend_id") REFERENCES "User" ("id"),
            FOREIGN KEY ("friend_status_id") REFERENCES "FriendStatus" ("id")
        );
    """
    )

    # --- Заполнение справочников ---

    # Вставляем типы расписаний
    daily_uuid = str(uuid.uuid4())
    weekly_uuid = str(uuid.uuid4())
    custom_uuid = str(uuid.uuid4())
    
    cursor.execute(
        "INSERT OR IGNORE INTO ScheduleType (id, name) VALUES (?, ?);",
        (daily_uuid, "daily"),
    )
    cursor.execute(
        "INSERT OR IGNORE INTO ScheduleType (id, name) VALUES (?, ?);",
        (weekly_uuid, "weekly"),
    )
    cursor.execute(
        "INSERT OR IGNORE INTO ScheduleType (id, name) VALUES (?, ?);",
        (custom_uuid, "custom"),
    )

    # Вставляем типы наград
    badge_uuid = str(uuid.uuid4())
    level_uuid = str(uuid.uuid4())
    challenge_uuid = str(uuid.uuid4())
    
    cursor.execute(
        "INSERT OR IGNORE INTO RewardType (id, name) VALUES (?, ?);",
        (badge_uuid, "badge"),
    )
    cursor.execute(
        "INSERT OR IGNORE INTO RewardType (id, name) VALUES (?, ?);",
        (level_uuid, "level"),
    )
    cursor.execute(
        "INSERT OR IGNORE INTO RewardType (id, name) VALUES (?, ?);",
        (challenge_uuid, "challenge"),
    )

    # Вставляем статусы дружбы
    pending_uuid = str(uuid.uuid4())
    accepted_uuid = str(uuid.uuid4())
    rejected_uuid = str(uuid.uuid4())
    
    cursor.execute(
        "INSERT OR IGNORE INTO FriendStatus (id, name) VALUES (?, ?);",
        (pending_uuid, "pending"),
    )
    cursor.execute(
        "INSERT OR IGNORE INTO FriendStatus (id, name) VALUES (?, ?);",
        (accepted_uuid, "accepted"),
    )
    cursor.execute(
        "INSERT OR IGNORE INTO FriendStatus (id, name) VALUES (?, ?);",
        (rejected_uuid, "rejected"),
    )

    # Создаем индексы для улучшения производительности
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_telegram_id ON User(telegram_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_habit_user_id ON Habit(user_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_habit_schedule_type ON Habit(schedule_type_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_completion_habit_id ON HabitCompletion(habit_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_completion_user_id ON HabitCompletion(user_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_completion_date ON HabitCompletion(completion_date);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_reward_user_id ON Reward(user_id);")

    # Подтверждаем изменения и закрываем соединение
    conn.commit()
    conn.close()

    print(f"[OK] База данных '{db_path}' успешно создана!")
    print("[INFO] Структура:")
    print("   - ScheduleType (daily, weekly, custom)")
    print("   - RewardType (badge, level, challenge)")
    print("   - FriendStatus (pending, accepted, rejected)")
    print("   - User (пользователи)")
    print("   - Habit (привычки с поддержкой custom расписания)")
    print("   - HabitCompletion (отметки выполнения)")
    print("   - Reward (награды)")
    print("   - Friend (дружба)")
    print("[INFO] Индексы созданы для оптимизации запросов")


def check_database_structure(db_path="habits_tracker.db"):
    """
    Проверяет структуру базы данных и выводит информацию о таблицах.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print(f"\n[INFO] Проверка структуры базы данных '{db_path}':")
    
    # Получаем список таблиц
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    print(f"\n[INFO] Найдено таблиц: {len(tables)}")
    for table in tables:
        table_name = table[0]
        print(f"\n[TABLE] {table_name}")
        
        # Получаем информацию о колонках
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = cursor.fetchall()
        
        for col in columns:
            col_id, name, type_name, not_null, default_val, pk = col
            nullable = "NOT NULL" if not_null else "NULL"
            primary = " (PRIMARY KEY)" if pk else ""
            default = f" DEFAULT {default_val}" if default_val else ""
            print(f"   - {name}: {type_name} {nullable}{default}{primary}")
        
        # Получаем количество записей
        cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
        count = cursor.fetchone()[0]
        print(f"   [COUNT] Записей: {count}")
    
    conn.close()


if __name__ == "__main__":
    # Создаем базу данных
    create_database()
    
    # Проверяем структуру
    check_database_structure()