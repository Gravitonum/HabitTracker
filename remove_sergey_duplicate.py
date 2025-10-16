"""
Скрипт для удаления дубликата привычки "Сделать разминку" у пользователя Sergey.
"""

import sqlite3


def remove_sergey_duplicate():
    """Удаляет дубликат привычки 'Сделать разминку' у пользователя Sergey."""
    conn = sqlite3.connect('habits_tracker.db')
    cursor = conn.cursor()
    
    try:
        # Получаем все привычки "Сделать разминку" у пользователя Sergey
        cursor.execute('''
            SELECT h.id, h.name, h.created_at
            FROM Habit h 
            JOIN User u ON h.user_id = u.id 
            WHERE u.first_name = 'Sergey' AND h.name = 'Сделать разминку'
            ORDER BY h.created_at DESC, h.id DESC
        ''')
        
        habits = cursor.fetchall()
        print(f"Найдено привычек 'Сделать разминку' у Sergey: {len(habits)}")
        
        if len(habits) > 1:
            # Оставляем только самую новую (первую в списке)
            keep_habit = habits[0]
            delete_habits = habits[1:]
            
            print(f"Оставляем привычку ID: {keep_habit[0][:8]}... (создана: {keep_habit[2]})")
            
            for habit_id, name, created_at in delete_habits:
                print(f"Удаляем привычку ID: {habit_id[:8]}... (создана: {created_at})")
                
                # Сначала удаляем связанные записи
                cursor.execute('DELETE FROM HabitCompletion WHERE habit_id = ?', (habit_id,))
                
                # Затем удаляем саму привычку
                cursor.execute('DELETE FROM Habit WHERE id = ?', (habit_id,))
            
            conn.commit()
            print("Дубликат удален!")
        else:
            print("Дубликатов не найдено")
        
        # Проверяем результат
        cursor.execute('''
            SELECT h.id, h.name
            FROM Habit h 
            JOIN User u ON h.user_id = u.id 
            WHERE u.first_name = 'Sergey' AND h.name = 'Сделать разминку'
        ''')
        
        remaining_habits = cursor.fetchall()
        print(f"\nОсталось привычек 'Сделать разминку' у Sergey: {len(remaining_habits)}")
        for habit_id, name in remaining_habits:
            print(f"  - {name} (ID: {habit_id[:8]}...)")
            
    except Exception as e:
        print(f"Ошибка: {e}")
        conn.rollback()
    finally:
        conn.close()


if __name__ == "__main__":
    remove_sergey_duplicate()
