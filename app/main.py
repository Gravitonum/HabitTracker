"""
Основная точка входа в приложение Telegram-бота.
"""

import asyncio
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, Application
from app.core.config import settings
from app.core.scheduler import HabitReminderScheduler
from app.bot.handlers.habits import (
    list_habits,
    create_habit_command,
    complete_habit,
    show_stats,
)
from app.bot.handlers.gamification import show_profile, show_rewards, show_leaderboard

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=getattr(logging, settings.LOG_LEVEL.upper()),
)
logger = logging.getLogger(__name__)


async def start(update, context) -> None:
    """Обработчик команды /start."""
    welcome_message = (
        "Привет! 👋\n"
        "Я бот для отслеживания привычек с элементами геймификации.\n\n"
        "Доступные команды:\n"
        "/profile - Посмотреть ваш профиль и статистику\n"
        "/habits - Список ваших привычек\n"
        "/create_habit - Создать новую привычку\n"
        "/complete - Отметить привычку как выполненную\n"
        "/stats - Статистика по привычкам\n"
        "/rewards - Ваши награды\n"
        "/leaderboard - Таблица лидеров\n"
        "/help - Помощь"
    )
    await update.message.reply_text(welcome_message)


async def help_command(update, context) -> None:
    """Обработчик команды /help."""
    help_text = (
        "Помощь по боту:\n\n"
        "1. /start - Начать работу с ботом\n"
        "2. /profile - Посмотреть уровень, очки, серию\n"
        "3. /habits - Увидеть список ваших привычек\n"
        "4. /create_habit Название - Создать новую привычку\n"
        "5. /complete Номер - Отметить привычку под указанным номером как выполненную\n"
        "6. /stats - Посмотреть подробную статистику по привычкам\n"
        "7. /rewards - Увидеть список ваших наград (бейджей)\n"
        "8. /leaderboard - Посмотреть таблицу лидеров по очкам\n"
        "9. /help - Показать это сообщение\n\n"
        "Создавайте привычки и отмечайте их выполнение, чтобы получать очки и награды!"
    )
    await update.message.reply_text(help_text)


async def setup_scheduler(application: Application):
    """
    Инициализирует и запускает планировщик задач.
    """
    scheduler = HabitReminderScheduler(application)
    await scheduler.start()
    # Сохраняем экземпляр планировщика в объекте приложения для возможной остановки
    application.bot_data["scheduler"] = scheduler


def main() -> None:
    """Запуск бота."""
    if not settings.TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN не установлен в переменных окружения.")
        return

    # Создание приложения
    application = ApplicationBuilder().token(settings.TELEGRAM_BOT_TOKEN).build()

    # Регистрация обработчиков команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("profile", show_profile))
    application.add_handler(CommandHandler("habits", list_habits))
    application.add_handler(CommandHandler("create_habit", create_habit_command))
    application.add_handler(CommandHandler("complete", complete_habit))
    application.add_handler(CommandHandler("stats", show_stats))
    application.add_handler(CommandHandler("rewards", show_rewards))
    application.add_handler(CommandHandler("leaderboard", show_leaderboard))

    # Добавление обработчика ошибок
    async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Логирование ошибок, возникающих в обработчиках."""
        logger.error(msg="Вызван исключение в обработчике", exc_info=context.error)

    application.add_error_handler(error_handler)

    # Инициализация планировщика задач при запуске приложения
    application.post_init = setup_scheduler

    # Запуск бота в режиме long polling
    logger.info("Запуск бота...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
