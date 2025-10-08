import sqlite3


def show_table_data(db_path="habits_tracker.db"):
    """
    Выводит меню выбора сущности и показывает первые 10 записей из выбранной таблицы.
    """
    # Словарь сопоставления названий сущностей и таблиц
    entity_map = {
        "1": "User",
        "2": "Habit",
        "3": "HabitCompletion",
        "4": "Reward",
        "5": "Friend",
        "6": "Challenge",
        "7": "ChallengeParticipant",
        "8": "Notification",
        "9": "ScheduleType",
        "10": "RewardType",
        "11": "FriendStatus",
    }

    while True:
        print("\n--- Меню просмотра таблиц ---")
        print("1. User")
        print("2. Habit")
        print("3. HabitCompletion")
        print("4. Reward")
        print("5. Friend")
        print("6. Challenge")
        print("7. ChallengeParticipant")
        print("8. Notification")
        print("9. ScheduleType")
        print("10. RewardType")
        print("11. FriendStatus")
        print("0. Выход")

        choice = input(
            "\nВыберите номер сущности для просмотра (или 0 для выхода): "
        ).strip()

        if choice == "0":
            print("Выход из программы.")
            break
        elif choice in entity_map:
            table_name = entity_map[choice]
            display_table(db_path, table_name)
        else:
            print("Неверный выбор. Пожалуйста, введите число от 0 до 11.")


def display_table(db_path, table_name):
    """
    Выводит первые 10 записей из указанной таблицы.
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Проверяем, существует ли таблица
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?;",
            (table_name,),
        )
        if not cursor.fetchone():
            print(f"\nОшибка: Таблица '{table_name}' не найдена в базе данных.")
            conn.close()
            return

        # Получаем названия столбцов
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns_info = cursor.fetchall()
        column_names = [
            info[1] for info in columns_info
        ]  # Индекс 1 соответствует имени столбца

        # Выполняем запрос на получение первых 10 записей
        cursor.execute(f"SELECT * FROM {table_name} LIMIT 10;")
        rows = cursor.fetchall()

        print(f"\n--- Содержимое таблицы '{table_name}' (первые 10 записей) ---")
        print(" | ".join(column_names))
        print(
            "-" * (len(" | ".join(column_names)) + len(column_names) - 1)
        )  # Добавляем разделитель

        if rows:
            for row in rows:
                print(
                    " | ".join(
                        str(value) if value is not None else "NULL" for value in row
                    )
                )
        else:
            print("Таблица пуста.")

        print(
            f"Всего записей в таблице '{table_name}': {cursor.execute(f'SELECT COUNT(*) FROM {table_name};').fetchone()[0]}"
        )

        conn.close()

    except sqlite3.Error as e:
        print(f"Ошибка при работе с базой данных: {e}")
    except Exception as e:
        print(f"Произошла непредвиденная ошибка: {e}")


if __name__ == "__main__":
    show_table_data()
