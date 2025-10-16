"""
Обработчики команд, связанных с геймификацией.
"""

from telegram import Update
from telegram.ext import ContextTypes
from app.bot.services.reward_service import get_user_rewards, get_user_level_info
from app.bot.services.habit_service import get_user_statistics
from app.bot.services.user_service import get_or_create_user, get_top_users_by_points, get_user_position_by_points
from app.core.database import get_db_session
import logging

logger = logging.getLogger(__name__)


async def show_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Показывает профиль пользователя с уровнем, очками и серией.
    """
    user = update.effective_user
    if not user:
        # Сначала проверяем, доступно ли сообщение
        if update.message:
            await update.message.reply_text(
                "Не удалось получить информацию о пользователе."
            )
        else:
            # Альтернативный способ отправки сообщения
            if update.effective_chat:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="Не удалось получить информацию о пользователе.",
                )
            else:
                logger.warning(
                    "Не удалось отправить сообщение: нет пользователя и чата"
                )
        return

    # Проверяем, что message существует
    if update.message is None:
        logger.warning(
            f"Получено обновление без сообщения для update_id {update.update_id}"
        )
        # Используем альтернативный способ отправки сообщения
        if update.effective_chat:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Не удалось отправить сообщение: обновление не содержит сообщения.",
            )
        return

    telegram_id = user.id

    try:
        async for db in get_db_session():
            # Убеждаемся, что пользователь зарегистрирован
            db_user = await get_or_create_user(
                db=db,
                telegram_id=telegram_id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name,
            )
            
            # Получаем статистику пользователя
            stats = await get_user_statistics(db, telegram_id)
            
            message = f"Профиль пользователя: {user.first_name or user.username or 'пользователь'}\n"
            message += f"Telegram ID: {telegram_id}\n"
            message += f"Уровень: {db_user.level}\n"
            message += f"Очки: {db_user.points}\n"
            message += f"Текущая серия: {db_user.current_streak} дней\n"
            message += f"Самая длинная серия: {db_user.longest_streak} дней\n"
            message += f"Дата регистрации: {db_user.created_at.strftime('%d.%m.%Y') if db_user.created_at else 'Неизвестно'}\n"
            message += "Награды: пока нет\n"
            message += "Чтобы посмотреть статистику привычек, используйте /stats"

            await update.message.reply_text(message)
            break
            
    except Exception as e:
        logger.error(f"Ошибка при получении профиля пользователя {telegram_id}: {e}")
        await update.message.reply_text("Произошла ошибка при получении профиля.")


async def show_rewards(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Показывает список наград пользователя.
    """
    user = update.effective_user
    if not user:
        # Используем context.bot для отправки сообщения, если update.message недоступен
        if update.effective_chat:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Не удалось получить информацию о пользователе.",
            )
        return

    # Проверяем, что message существует
    if update.message is None:
        logger.warning(
            f"Получено обновление без сообщения для update_id {update.update_id}"
        )
        # Используем альтернативный способ отправки сообщения
        if update.effective_chat:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Не удалось отправить сообщение: обновление не содержит сообщения.",
            )
        return

    telegram_id = user.id

    # Пример получения данных (требует интеграции с базой данных)
    # rewards = await get_user_rewards(db_session, telegram_id)

    # Пока временный ответ
    message = f"Награды пользователя {user.full_name}:\n"
    message += "Пока нет наград. Выполняйте привычки, чтобы их получить!"

    await update.message.reply_text(message)


async def show_leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Показывает таблицу лидеров (по умолчанию по очкам).
    """
    user = update.effective_user
    if not user:
        if update.effective_chat:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Не удалось получить информацию о пользователе.",
            )
        return

    # Проверяем, что message существует
    if update.message is None:
        logger.warning(
            f"Получено обновление без сообщения для update_id {update.update_id}"
        )
        # Используем альтернативный способ отправки сообщения
        if update.effective_chat:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Не удалось отправить сообщение: обновление не содержит сообщения.",
            )
        return

    telegram_id = user.id

    try:
        async for db in get_db_session():
            # Получаем топ пользователей по очкам
            leaderboard = await get_top_users_by_points(db, limit=10)
            
            # Получаем позицию текущего пользователя
            user_position = await get_user_position_by_points(db, telegram_id)
            
            if not leaderboard:
                message = "🏆 Таблица лидеров (по очкам):\n\n"
                message += "Пока никто не набрал очков. Станьте первым!\n"
                message += "Выполняйте привычки, чтобы заработать очки и попасть в таблицу лидеров."
            else:
                message = "🏆 Таблица лидеров (по очкам):\n\n"
                
                for user_data, position in leaderboard:
                    # Формируем имя пользователя
                    display_name = user_data.first_name or user_data.username or f"Пользователь {user_data.telegram_id}"
                    if user_data.last_name:
                        display_name += f" {user_data.last_name}"
                    
                    # Добавляем эмодзи для топ-3
                    if position == 1:
                        medal = "🥇"
                    elif position == 2:
                        medal = "🥈"
                    elif position == 3:
                        medal = "🥉"
                    else:
                        medal = f"{position}."
                    
                    message += f"{medal} {display_name} - {user_data.points} очков\n"
                
                # Добавляем информацию о позиции текущего пользователя
                message += "\n"
                if user_position:
                    if user_position <= 10:
                        message += f"🎯 Ваше место: {user_position} (уже в топе!)"
                    else:
                        message += f"🎯 Ваше место: {user_position}"
                else:
                    message += "🎯 Ваше место: не найдено (наберите очки!)"

            await update.message.reply_text(message)
            break
            
    except Exception as e:
        logger.error(f"Ошибка при получении таблицы лидеров: {e}")
        await update.message.reply_text("Произошла ошибка при получении таблицы лидеров.")
