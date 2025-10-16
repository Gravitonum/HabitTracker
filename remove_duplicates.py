"""
Скрипт для удаления дублирующихся привычек.
"""

import sqlite3


def remove_duplicate_habits():
    """Удаляет дублирующиеся привычки, оставляя только самую новую."""
    conn = sqlite3.connect('habits_tracker.db')
    cursor = conn.cursor()
    
    try:
        # Находим дубликаты для каждого пользователя
        cursor.execute('''
            SELECT u.id, h.name, COUNT(*) as count
            FROM User u 
            JOIN Habit h ON u.id = h.user_id 
            WHERE h.is_active = 1
            GROUP BY u.id, h.name
            HAVING COUNT(*) > 1
        ''')
        
        duplicates = cursor.fetchall()
        
        if not duplicates:
            print("Дублирующихся привычек не найдено")
            return
        
        print("Найдены дублирующиеся привычки:")
        for user_id, habit_name, count in duplicates:
            print(f"  Пользователь {user_id}: {habit_name} - {count} раз")
        
        # Удаляем дубликаты, оставляя только самую новую (с максимальным ID)
        for user_id, habit_name, count in duplicates:
            print(f"\nОбрабатываем дубликаты для '{habit_name}' пользователя {user_id}...")
            
            # Получаем все ID привычек с таким именем для этого пользователя
            cursor.execute('''
                SELECT h.id, h.created_at
                FROM Habit h 
                WHERE h.user_id = ? AND h.name = ? AND h.is_active = 1
                ORDER BY h.created_at DESC, h.id DESC
            ''', (user_id, habit_name))
            
            habits = cursor.fetchall()
            
            # Оставляем только самую новую, остальные удаляем
            if len(habits) > 1:
                keep_habit = habits[0]  # Самая новая
                delete_habits = habits[1:]  # Остальные
                
                print(f"  Оставляем привычку ID: {keep_habit[0][:8]}...")
                
                for habit_id, created_at in delete_habits:
                    print(f"  Удаляем привычку ID: {habit_id[:8]}...")
                    
                    # Сначала удаляем связанные записи
                    cursor.execute('DELETE FROM HabitCompletion WHERE habit_id = ?', (habit_id,))
                    
                    # Затем удаляем саму привычку
                    cursor.execute('DELETE FROM Habit WHERE id = ?', (habit_id,))
        
        conn.commit()
        print("\nДубликаты успешно удалены!")
        
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
    remove_duplicate_habits()
