"""
Утилиты для расчёта серий (streaks).
"""

from datetime import date, timedelta
from typing import List, Optional
from app.models.database import HabitCompletion


def calculate_total_points_for_completion(habit, streak_increment: int) -> int:
    """
    Рассчитывает общее количество очков за выполнение привычки.
    habit — объект привычки (ожидается, что у него есть атрибут base_points).
    streak_increment — текущий бонус за серию.
    """
    base_points = getattr(habit, "base_points", 10)  # 10 по умолчанию
    streak_bonus = (
        max(0, streak_increment - 1) * 2
    )  # например, +2 за каждый день после первого
    return base_points + streak_bonus


def calculate_current_streak(
    completions: List[HabitCompletion], today: Optional[date] = None
) -> int:
    """
    Рассчитывает текущую серию (количество дней подряд, включая сегодня, если привычка выполнена).
    Сортирует отметки по дате и проверяет последовательность.
    """
    if not completions:
        return 0

    if today is None:
        today = date.today()

    # Создаем словарь для быстрого доступа к статусу выполнения по дате
    completion_dict = {}
    for comp in completions:
        # Извлекаем значения из SQLAlchemy объекта
        comp_date = comp.completion_date
        is_completed = comp.is_completed

        # Преобразуем в обычный bool, обрабатывая None
        if is_completed is None:
            is_completed_bool = False
        else:
            # Для SQLAlchemy полей используем явное сравнение
            is_completed_bool = bool(is_completed)

        completion_dict[comp_date] = is_completed_bool

    # Получаем все даты, сортируем по убыванию
    all_dates = sorted(completion_dict.keys(), reverse=True)

    current_streak = 0
    current_date = today

    # Проверяем сегодняшний день
    if today in completion_dict and completion_dict[today]:
        current_streak = 1
        current_date = today - timedelta(days=1)
    else:
        return 0

    # Продолжаем проверять предыдущие дни
    while current_date in completion_dict and completion_dict[current_date]:
        current_streak += 1
        current_date -= timedelta(days=1)

    return current_streak


def calculate_longest_streak(completions: List[HabitCompletion]) -> int:
    """
    Рассчитывает самую длинную серию за всё время.
    """
    if not completions:
        return 0

    # Собираем все даты, когда привычка была выполнена
    completed_dates = []
    for comp in completions:
        if comp.is_completed is not None:
            # Для SQLAlchemy полей используем явное сравнение
            if bool(comp.is_completed):
                completed_dates.append(comp.completion_date)

    if not completed_dates:
        return 0

    # Убираем дубликаты и сортируем
    completed_dates = sorted(set(completed_dates))

    if len(completed_dates) == 1:
        return 1

    longest = 1
    current = 1

    for i in range(1, len(completed_dates)):
        # Если даты идут подряд
        if completed_dates[i] == completed_dates[i - 1] + timedelta(days=1):
            current += 1
        else:
            # Серия прервалась, проверяем максимальную
            longest = max(longest, current)
            current = 1

    # Проверяем последнюю серию
    longest = max(longest, current)

    return longest


def update_streak_increment(
    habit_id: str,
    user_id: str,
    completion_date: date,
    all_completions_for_habit: List[HabitCompletion],
) -> int:
    """
    Рассчитывает значение streak_increment для новой отметки.
    Это значение используется для начисления бонусных очков.
    """
    # Фильтруем отметки для конкретной привычки и пользователя
    habit_completions = [
        c
        for c in all_completions_for_habit
        if c.habit_id == habit_id and c.user_id == user_id
    ]

    if not habit_completions:
        return 1

    # Создаем список с извлеченными данными
    completion_list = []
    for comp in habit_completions:
        # Извлекаем значения из SQLAlchemy объектов
        comp_date = comp.completion_date
        is_completed = comp.is_completed
        streak_inc = comp.streak_increment

        # Преобразуем в обычные типы
        is_completed_bool = bool(is_completed) if is_completed is not None else False
        streak_inc_int = int(streak_inc) if streak_inc is not None else 0

        completion_list.append(
            {
                "date": comp_date,
                "is_completed": is_completed_bool,
                "streak_increment": streak_inc_int,
            }
        )

    # Сортируем по дате (старые первыми)
    completion_list.sort(key=lambda x: x["date"])

    # Находим последнюю выполненную отметку до текущей даты
    last_completed = None
    for comp in reversed(completion_list):
        if comp["date"] < completion_date and comp["is_completed"]:
            last_completed = comp
            break

    # Если нет предыдущей выполненной отметки
    if last_completed is None:
        # Проверяем, можем ли мы продолжить серию с последней отметки
        last_comp = completion_list[-1]
        if (
            last_comp["date"] == completion_date - timedelta(days=1)
            and last_comp["is_completed"]
        ):
            return last_comp["streak_increment"] + 1
        else:
            return 1
    else:
        # Проверяем, является ли текущая дата следующей за последней выполненной
        if last_completed["date"] == completion_date - timedelta(days=1):
            return last_completed["streak_increment"] + 1
        else:
            return 1
