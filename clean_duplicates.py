"""
Скрипт для очистки оставшихся дубликатов.
"""

import sqlite3


def clean_remaining_duplicates():
    """Удаляет оставшиеся дубликаты привычек."""
    conn = sqlite3.connect('habits_tracker.db')
    cursor = conn.cursor()
    
    try:
        # Находим все привычки "Сделать разминку" у пользователя Sergey
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
            
            print(f"Оставляем привычку ID: {keep_habit[0][:8]}...")
            
            for habit_id, name, created_at in delete_habits:
                print(f"Удаляем привычку ID: {habit_id[:8]}...")
                
                # Сначала удаляем связанные записи
                cursor.execute('DELETE FROM HabitCompletion WHERE habit_id = ?', (habit_id,))
                
                # Затем удаляем саму привычку
                cursor.execute('DELETE FROM Habit WHERE id = ?', (habit_id,))
            
            conn.commit()
            print("Дубликаты удалены!")
        else:
            print("Дубликатов не найдено")
        
        # Проверяем результат
        cursor.execute('''
            SELECT u.first_name, h.name, COUNT(*) as count
            FROM User u 
            JOIN Habit h ON u.id = h.user_id 
            WHERE h.is_active = 1
            GROUP BY u.id, h.name
            HAVING COUNT(*) > 1
        ''')
        
        remaining_duplicates = cursor.fetchall()
        if remaining_duplicates:
            print("Остались дубликаты:")
            for user_name, habit_name, count in remaining_duplicates:
                print(f"  {user_name}: {habit_name} - {count} раз")
        else:
            print("Все дубликаты удалены!")
            
    except Exception as e:
        print(f"Ошибка: {e}")
        conn.rollback()
    finally:
        conn.close()


if __name__ == "__main__":
    clean_remaining_duplicates()
