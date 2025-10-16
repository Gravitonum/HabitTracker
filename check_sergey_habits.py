"""
Скрипт для проверки привычек пользователя Sergey.
"""

import sqlite3


def check_sergey_habits():
    """Проверяет привычки пользователя Sergey."""
    conn = sqlite3.connect('habits_tracker.db')
    cursor = conn.cursor()
    
    try:
        # Получаем все привычки пользователя Sergey
        cursor.execute('''
            SELECT h.id, h.name, h.is_active, h.custom_schedule_days, h.custom_schedule_time
            FROM Habit h 
            JOIN User u ON h.user_id = u.id 
            WHERE u.first_name = 'Sergey'
            ORDER BY h.name, h.id
        ''')
        
        habits = cursor.fetchall()
        print(f"Привычки пользователя Sergey ({len(habits)}):")
        
        for habit_id, name, is_active, days, time in habits:
            status = "активна" if is_active else "неактивна"
            print(f"  - {name} (ID: {habit_id[:8]}...) - {status}")
            if days or time:
                print(f"    Дни: {days}, Время: {time}")
        
        # Проверяем дубликаты по имени
        cursor.execute('''
            SELECT h.name, COUNT(*) as count
            FROM Habit h 
            JOIN User u ON h.user_id = u.id 
            WHERE u.first_name = 'Sergey' AND h.is_active = 1
            GROUP BY h.name
            HAVING COUNT(*) > 1
        ''')
        
        duplicates = cursor.fetchall()
        if duplicates:
            print("\nДубликаты:")
            for name, count in duplicates:
                print(f"  {name}: {count} раз")
        else:
            print("\nДубликатов не найдено")
            
    except Exception as e:
        print(f"Ошибка: {e}")
    finally:
        conn.close()


if __name__ == "__main__":
    check_sergey_habits()
