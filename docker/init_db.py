#!/usr/bin/env python3
"""
Скрипт для инициализации базы данных в Docker контейнере.
"""

import os
import sys
import asyncio
from pathlib import Path

# Добавляем путь к приложению
sys.path.append('/app')

from create_database import create_database


def init_database():
    """Инициализирует базу данных."""
    print("Инициализация базы данных...")
    
    # Создаем директорию для базы данных
    data_dir = Path("/app/data")
    data_dir.mkdir(exist_ok=True)
    
    # Создаем базу данных с помощью существующего скрипта
    db_path = "/app/data/habits_tracker.db"
    
    # Проверяем, существует ли уже база данных
    if not Path(db_path).exists():
        print(f"Создание новой базы данных: {db_path}")
        create_database(db_path)
        print("База данных успешно создана!")
    else:
        print(f"База данных уже существует: {db_path}")
    
    # Проверяем структуру базы данных
    try:
        import sqlite3
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Проверяем наличие таблицы User
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='User';")
        if cursor.fetchone():
            print("✓ Таблица User найдена")
        else:
            print("✗ Таблица User не найдена, пересоздаем базу данных...")
            conn.close()
            os.remove(db_path)
            create_database(db_path)
            print("База данных пересоздана!")
        
        conn.close()
        
    except Exception as e:
        print(f"Ошибка при проверке базы данных: {e}")
        print("Пересоздаем базу данных...")
        if Path(db_path).exists():
            os.remove(db_path)
        create_database(db_path)
        print("База данных пересоздана!")


if __name__ == "__main__":
    init_database()
