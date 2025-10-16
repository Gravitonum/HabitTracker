"""
Скрипт для проверки дублирующихся привычек.
"""

import sqlite3


def check_duplicate_habits():
    """Проверяет дублирующиеся привычки в базе данных."""
    conn = sqlite3.connect('habits_tracker.db')
    cursor = conn.cursor()
    
    try:
        # Получаем всех пользователей с их привычками
        cursor.execute('''
            SELECT u.first_name, u.telegram_id, h.name, h.id, h.is_active
            FROM User u 
            JOIN Habit h ON u.id = h.user_id 
            ORDER BY u.first_name, h.name
        ''')
        
        users_habits = cursor.fetchall()
        
        print("Все пользователи и их привычки:")
        current_user = None
        for user_first_name, telegram_id, habit_name, habit_id, is_active in users_habits:
            if current_user != user_first_name:
                current_user = user_first_name
                print(f"\nПользователь: {user_first_name} (ID: {telegram_id})")
            
            status = "активна" if is_active else "неактивна"
            print(f"  - {habit_name} (ID: {habit_id[:8]}...) - {status}")
        
        # Проверяем дубликаты
        print("\n\nПроверка дубликатов:")
        cursor.execute('''
            SELECT u.first_name, h.name, COUNT(*) as count
            FROM User u 
            JOIN Habit h ON u.id = h.user_id 
            WHERE h.is_active = 1
            GROUP BY u.id, h.name
            HAVING COUNT(*) > 1
        ''')
        
        duplicates = cursor.fetchall()
        if duplicates:
            print("Найдены дублирующиеся привычки:")
            for user_name, habit_name, count in duplicates:
                print(f"  {user_name}: {habit_name} - {count} раз")
        else:
            print("Дублирующихся привычек не найдено")
            
    except Exception as e:
        print(f"Ошибка: {e}")
    finally:
        conn.close()


if __name__ == "__main__":
    check_duplicate_habits()
