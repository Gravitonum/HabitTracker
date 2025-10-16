"""
Утилиты для работы с часовыми поясами.
"""

from datetime import datetime, time
from zoneinfo import ZoneInfo
from typing import Optional


def get_user_timezone(user_timezone: Optional[str] = None) -> ZoneInfo:
    """
    Возвращает объект часового пояса пользователя.
    По умолчанию используется Europe/Moscow.
    """
    if user_timezone:
        try:
            return ZoneInfo(user_timezone)
        except Exception:
            # Если часовой пояс неверный, используем Moscow
            pass
    return ZoneInfo("Europe/Moscow")


def convert_time_to_utc(time_str: str, user_timezone: Optional[str] = None) -> time:
    """
    Конвертирует время пользователя в UTC.
    
    Args:
        time_str: Время в формате "HH:MM" в часовом поясе пользователя
        user_timezone: Часовой пояс пользователя
    
    Returns:
        time: Время в UTC
    """
    user_tz = get_user_timezone(user_timezone)
    
    # Парсим время
    hour, minute = map(int, time_str.split(':'))
    user_time = time(hour, minute)
    
    # Создаем datetime с сегодняшней датой в часовом поясе пользователя
    today = datetime.now(user_tz).date()
    user_datetime = datetime.combine(today, user_time).replace(tzinfo=user_tz)
    
    # Конвертируем в UTC
    utc_datetime = user_datetime.astimezone(ZoneInfo("UTC"))
    
    return utc_datetime.time()


def get_current_time_in_user_timezone(user_timezone: Optional[str] = None) -> datetime:
    """
    Возвращает текущее время в часовом поясе пользователя.
    """
    user_tz = get_user_timezone(user_timezone)
    return datetime.now(user_tz)


def is_habit_time_now(habit_time: str, user_timezone: Optional[str] = None, tolerance_minutes: int = 5) -> bool:
    """
    Проверяет, наступило ли время для привычки.
    
    Args:
        habit_time: Время привычки в формате "HH:MM"
        user_timezone: Часовой пояс пользователя
        tolerance_minutes: Допустимое отклонение в минутах
    
    Returns:
        bool: True, если время наступило
    """
    user_tz = get_user_timezone(user_timezone)
    current_time = datetime.now(user_tz)
    
    # Парсим время привычки
    hour, minute = map(int, habit_time.split(':'))
    habit_time_obj = time(hour, minute)
    current_time_obj = current_time.time()
    
    # Вычисляем разность в минутах
    current_minutes = current_time_obj.hour * 60 + current_time_obj.minute
    habit_minutes = habit_time_obj.hour * 60 + habit_time_obj.minute
    
    diff_minutes = abs(current_minutes - habit_minutes)
    
    return diff_minutes <= tolerance_minutes


def get_weekday_name(weekday_number: int) -> str:
    """
    Возвращает название дня недели по номеру.
    0 = понедельник, 6 = воскресенье
    """
    weekdays = ["пн", "вт", "ср", "чт", "пт", "сб", "вс"]
    return weekdays[weekday_number] if 0 <= weekday_number <= 6 else "неизвестно"


def is_habit_day_today(habit_days: str, user_timezone: Optional[str] = None) -> bool:
    """
    Проверяет, должен ли выполняться привычка сегодня.
    
    Args:
        habit_days: Дни недели в формате "пн,вт,ср" или "чт"
        user_timezone: Часовой пояс пользователя
    
    Returns:
        bool: True, если сегодня день для привычки
    """
    user_tz = get_user_timezone(user_timezone)
    current_weekday = datetime.now(user_tz).weekday()  # 0 = понедельник, 6 = воскресенье
    
    # Преобразуем в русские названия
    current_day_name = get_weekday_name(current_weekday)
    
    # Проверяем, есть ли сегодняшний день в списке дней привычки
    habit_days_list = [day.strip() for day in habit_days.split(',')]
    return current_day_name in habit_days_list
