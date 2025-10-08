"""
Утилиты для расчёта серий (streaks).
"""

from datetime import date, timedelta
from typing import List, Optional
from app.models.database import HabitCompletion


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

    # Сортируем отметки по дате (новые первыми)
    sorted_completions = sorted(
        completions, key=lambda x: x.completion_date, reverse=True
    )

    current_streak = 0
    expected_date = today

    for completion in sorted_completions:
        # Извлекаем значения из SQLAlchemy полей
        completion_date = completion.completion_date
        is_completed = completion.is_completed

        # Пропускаем отметки с будущими датами
        if completion_date > today:
            continue

        # Если дата совпадает и выполнено, увеличиваем серию
        if completion_date == expected_date and is_completed:
            current_streak += 1
            expected_date -= timedelta(days=1)
        # Если дата совпадает, но не выполнено - серия обрывается
        elif completion_date == expected_date and not is_completed:
            break
        # Если между датами пропуск - серия обрывается
        elif completion_date < expected_date:
            # Проверяем, была ли дата выполнена
            # Если нет отметки на expected_date, и completion_date < expected_date, серия обрывается
            # Но если completion_date == expected_date - 1 и выполнено, то продолжаем
            # Если completion_date < expected_date - 1, то пропуск, серия обрывается
            if completion_date == expected_date - timedelta(days=1) and is_completed:
                # Продолжаем серию, но переходим к следующей дате
                current_streak += 1
                expected_date = completion_date - timedelta(days=1)
            else:
                # Пропуск более чем на 1 день или дата не выполнена
                break

    return current_streak


def calculate_longest_streak(completions: List[HabitCompletion]) -> int:
    """
    Рассчитывает самую длинную серию за всё время.
    Это более сложная логика, требующая перебора всех возможных серий.
    """
    if not completions:
        return 0

    # Получаем все уникальные даты выполнения, отсортированные по возрастанию
    completed_dates = sorted(
        {comp.completion_date for comp in completions if comp.is_completed}
    )

    if not completed_dates:
        return 0

    # Если есть только одна дата выполнения
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
            current = 1  # Начинаем новую серию

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

    # Сортируем по дате (старые первыми для анализа последовательности)
    sorted_completions = sorted(habit_completions, key=lambda x: x.completion_date)

    # Если это первая отметка для привычки
    if not sorted_completions:
        return 1

    # Находим последнюю отметку до текущей даты
    previous_completion = None
    for comp in reversed(sorted_completions):
        if comp.completion_date < completion_date:
            previous_completion = comp
            break

    # Если нет предыдущей отметки до сегодняшней даты
    if previous_completion is None:
        # Проверяем, является ли сегодняшняя дата следующей после последней возможной отметки
        last_completion = sorted_completions[-1]
        last_date = last_completion.completion_date
        is_completed = last_completion.is_completed
        streak_increment = last_completion.streak_increment

        if completion_date == last_date + timedelta(days=1) and is_completed:
            return streak_increment + 1
        else:
            # Прерывание серии или начало новой
            return 1
    else:
        # Есть предыдущая отметка до сегодняшней даты
        is_completed = previous_completion.is_completed
        streak_increment = previous_completion.streak_increment

        if (
            completion_date == previous_completion.completion_date + timedelta(days=1)
            and is_completed
        ):
            # Продолжение серии
            return streak_increment + 1
        else:
            # Прерывание серии
            return 1
