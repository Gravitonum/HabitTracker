"""
Скрипт для обновления существующей базы данных - добавление полей timezone.
"""

import sqlite3
import os


def update_database_timezone(db_path="habits_tracker.db"):
    """
    Добавляет поля timezone в существующую базу данных.
    """
    if not os.path.exists(db_path):
        print(f"[ERROR] База данных '{db_path}' не найдена!")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Проверяем, есть ли уже поле timezone в таблице User
        cursor.execute("PRAGMA table_info(User);")
        user_columns = [col[1] for col in cursor.fetchall()]
        
        if "timezone" not in user_columns:
            print("[INFO] Добавляем поле timezone в таблицу User...")
            cursor.execute("ALTER TABLE User ADD COLUMN timezone TEXT DEFAULT 'Europe/Moscow';")
            print("[OK] Поле timezone добавлено в таблицу User")
        else:
            print("[INFO] Поле timezone уже существует в таблице User")
        
        # Проверяем, есть ли уже поле timezone в таблице Habit
        cursor.execute("PRAGMA table_info(Habit);")
        habit_columns = [col[1] for col in cursor.fetchall()]
        
        if "timezone" not in habit_columns:
            print("[INFO] Добавляем поле timezone в таблицу Habit...")
            cursor.execute("ALTER TABLE Habit ADD COLUMN timezone TEXT DEFAULT 'Europe/Moscow';")
            print("[OK] Поле timezone добавлено в таблицу Habit")
        else:
            print("[INFO] Поле timezone уже существует в таблице Habit")
        
        # Обновляем существующие записи, устанавливая timezone для всех пользователей и привычек
        print("[INFO] Обновляем существующие записи...")
        cursor.execute("UPDATE User SET timezone = 'Europe/Moscow' WHERE timezone IS NULL;")
        cursor.execute("UPDATE Habit SET timezone = 'Europe/Moscow' WHERE timezone IS NULL;")
        
        # Подтверждаем изменения
        conn.commit()
        print("[OK] База данных успешно обновлена!")
        
        # Показываем статистику
        cursor.execute("SELECT COUNT(*) FROM User;")
        user_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM Habit;")
        habit_count = cursor.fetchone()[0]
        
        print(f"[INFO] Обновлено пользователей: {user_count}")
        print(f"[INFO] Обновлено привычек: {habit_count}")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Ошибка при обновлении базы данных: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def check_database_structure(db_path="habits_tracker.db"):
    """
    Проверяет структуру базы данных и выводит информацию о таблицах.
    """
    if not os.path.exists(db_path):
        print(f"[ERROR] База данных '{db_path}' не найдена!")
        return
    
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
    print("=== Обновление базы данных - добавление поддержки часовых поясов ===")
    
    # Обновляем базу данных
    success = update_database_timezone()
    
    if success:
        # Проверяем структуру
        check_database_structure()
        print("\n[OK] Обновление завершено успешно!")
    else:
        print("\n[ERROR] Обновление не удалось!")
