"""
Обработчики команд, связанных с привычками.
"""

from telegram import Update
from telegram.ext import ContextTypes
from app.bot.services.habit_service import (
    create_habit,
    get_user_habits,
    get_user_statistics,
    mark_habit_completed,
    get_habit_by_id,
)
from app.bot.services.reward_service import award_points_and_rewards
from app.utils.points_calculator import calculate_total_points_for_completion
from app.utils.streak_calculator import update_streak_increment
from app.core.database import get_db_session
from datetime import date
import logging

logger = logging.getLogger(__name__)


async def _send_reply(update: Update, text: str):
    """Вспомогательная функция для отправки сообщений"""
    try:
        if update.message:
            await update.message.reply_text(text)
        elif update.callback_query:
            # Для callback_query всегда используем effective_chat
            if update.effective_chat:
                await update.effective_chat.send_message(text)
            elif update.effective_user:
                # Если effective_chat недоступен, используем bot с ID пользователя
                await update.get_bot().send_message(
                    chat_id=update.effective_user.id, text=text
                )
            else:
                logger.error(
                    "Не удалось отправить сообщение: нет доступного чата или пользователя"
                )
        else:
            # Используем effective_chat как запасной вариант
            if update.effective_chat:
                await update.effective_chat.send_message(text)
            elif update.effective_user:
                await update.get_bot().send_message(
                    chat_id=update.effective_user.id, text=text
                )
            else:
                logger.error(
                    "Не удалось отправить сообщение: нет доступного чата или пользователя"
                )
    except Exception as e:
        logger.error(f"Ошибка при отправке сообщения: {e}")
        # Финальная попытка
        try:
            if update.effective_user:
                await update.get_bot().send_message(
                    chat_id=update.effective_user.id, text=text
                )
            else:
                logger.error(
                    "Критическая ошибка: невозможно отправить сообщение - нет пользователя"
                )
        except Exception as final_error:
            logger.error(f"Критическая ошибка при отправке сообщения: {final_error}")


async def list_habits(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Показывает список привычек пользователя.
    """
    user = update.effective_user
    if not user:
        await _send_reply(update, "Не удалось получить информацию о пользователе.")
        return

    telegram_id = user.id

    # Пример получения данных (требует интеграции с базой данных)
    # async with get_db_session() as db:
    #     habits = await get_user_habits(db, telegram_id)

    # Пока временный ответ
    message = f"Список ваших привычек, {user.full_name}:\n"
    message += "1. Пить воду (ежедневно)\n"
    message += "2. Приседания (ежедневно)\n"
    message += (
        "Чтобы отметить привычку, используйте /complete <номер> или кнопки (в будущем)"
    )

    await _send_reply(update, message)


async def create_habit_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Команда для создания новой привычки.
    Пример использования: /create_habit Название привычки - описание
    """
    user = update.effective_user
    if not user:
        await _send_reply(update, "Не удалось получить информацию о пользователе.")
        return

    if not context.args:
        await _send_reply(
            update,
            "Пожалуйста, укажите название привычки. Пример: /create_habit Пить воду - Ежедневно пить 2 литра воды",
        )
        return

    command_text = " ".join(context.args)
    parts = command_text.split(" - ", 1)
    name = parts[0].strip()
    description = parts[1].strip() if len(parts) > 1 else ""

    if not name:
        await _send_reply(update, "Название привычки не может быть пустым.")
        return

    # Пример создания (требует интеграции с базой данных)
    # async with get_db_session() as db:
    #     new_habit = await create_habit(db, telegram_id=user.id, name=name, description=description)

    # Пока временный ответ
    message = f"Привычка '{name}' успешно создана!\nОписание: {description}\nТип расписания: ежедневно (по умолчанию)\nБазовые очки: 10"
    await _send_reply(update, message)


async def complete_habit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Отмечает привычку как выполненную.
    Пример использования: /complete 1
    """
    user = update.effective_user
    if not user:
        await _send_reply(update, "Не удалось получить информацию о пользователе.")
        return

    if not context.args or len(context.args) != 1:
        await _send_reply(
            update, "Пожалуйста, укажите номер привычки. Пример: /complete 1"
        )
        return

    try:
        habit_number = int(context.args[0])
    except ValueError:
        await _send_reply(update, "Номер привычки должен быть числом.")
        return

    # Пример получения и обновления данных (требует интеграции с базой данных)
    # async with get_db_session() as db:
    #     # Получаем список привычек пользователя
    #     user_habits = await get_user_habits(db, user.id)
    #     if habit_number <= 0 or habit_number > len(user_habits):
    #         await update.message.reply_text(f"Привычка с номером {habit_number} не найдена.")
    #         return
    #
    #     selected_habit = user_habits[habit_number - 1]
    #     # Получаем все отметки для этой привычки
    #     all_completions = await get_all_completions_for_habit(db, selected_habit.id)
    #     # Рассчитываем streak_increment
    #     streak_val = update_streak_increment(selected_habit.id, user.id, date.today(), all_completions)
    #     # Отмечаем выполнение
    #     completion = await mark_habit_completed(db, selected_habit.id, user.id, date.today(), streak_val)
    #     # Рассчитываем и начисляем очки
    #     points_earned = calculate_total_points_for_completion(selected_habit, streak_val)
    #     await award_points_and_rewards(db, user.id, points_earned, streak_val)

    # Пока временный ответ
    message = (
        f"Привычка под номером {habit_number} отмечена как выполненная на сегодня!\n"
    )
    message += f"Вы получили 10 очков (и, возможно, бонус за серию)."
    await _send_reply(update, message)


async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Показывает статистику по привычкам пользователя.
    """
    user = update.effective_user
    if not user:
        await _send_reply(update, "Не удалось получить информацию о пользователе.")
        return

    telegram_id = user.id

    # Пример получения данных (требует интеграции с базой данных)
    # async with get_db_session() as db:
    #     stats = await get_user_statistics(db, telegram_id)

    # Пока временный ответ
    message = f"Статистика привычек для {user.full_name}:\n"
    message += "Привычка 'Пить воду': выполнена 5 дней подряд\n"
    message += "Привычка 'Приседания': выполнена 2 дня подряд\n"
    message += "Общий прогресс: 75%"

    await _send_reply(update, message)
