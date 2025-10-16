"""
Скрипт для исправления формата UUID в базе данных.
"""

import sqlite3


def fix_uuid_format():
    """Исправляет формат UUID в таблице ScheduleType."""
    conn = sqlite3.connect('habits_tracker.db')
    cursor = conn.cursor()
    
    try:
        # Обновляем UUID в таблице ScheduleType, убирая дефисы
        cursor.execute('UPDATE ScheduleType SET id = "aba8bdc339414bb3900055977fc1369e" WHERE name = "daily"')
        cursor.execute('UPDATE ScheduleType SET id = "5059ca09c319425baa8fe9a19a7a0fb1" WHERE name = "weekly"')
        cursor.execute('UPDATE ScheduleType SET id = "0fef53cd7a39460dbc99d85da28a6f74" WHERE name = "custom"')
        
        conn.commit()
        print("UUID в таблице ScheduleType обновлены")
        
        # Проверяем результат
        cursor.execute('SELECT * FROM ScheduleType')
        schedule_types = cursor.fetchall()
        print("Обновленные типы расписания:")
        for st in schedule_types:
            print(f"  {st[0]} - {st[1]}")
        
        # Проверяем JOIN
        cursor.execute('SELECT h.name, h.is_active, st.name FROM Habit h JOIN ScheduleType st ON h.schedule_type_id = st.id WHERE h.is_active = 1')
        habits = cursor.fetchall()
        print(f"\nАктивные привычки после исправления ({len(habits)}):")
        for h in habits:
            print(f"  {h[0]} - активна: {h[1]} - тип: {h[2]}")
        
    except Exception as e:
        print(f"Ошибка: {e}")
        conn.rollback()
    finally:
        conn.close()


if __name__ == "__main__":
    fix_uuid_format()
