"""
Основная точка входа в приложение Telegram-бота.
"""

import asyncio
import logging
from telegram import Update, BotCommand
from telegram.ext import ApplicationBuilder, CommandHandler, ConversationHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, Application
from app.core.config import settings
from app.core.scheduler import HabitReminderScheduler
from app.bot.handlers.habits import (
    list_habits,
    create_habit_command,
    complete_habit,
    handle_complete_callback,
    delete_habit,
    handle_delete_callback,
    handle_delete_confirm_callback,
    show_stats,
    test_notifications,
)
from app.bot.handlers.conversation import (
    start_create_habit,
    handle_schedule_type,
    handle_custom_settings,
    handle_habit_name,
    handle_habit_description,
    cancel_create_habit,
    SCHEDULE_TYPE,
    HABIT_NAME,
    HABIT_DESCRIPTION,
    CUSTOM_SETTINGS,
)
from app.bot.handlers.gamification import show_profile, show_rewards, show_leaderboard
from app.bot.services.user_service import get_or_create_user
from app.core.database import get_db_session

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=getattr(logging, settings.LOG_LEVEL.upper()),
)
logger = logging.getLogger(__name__)


async def setup_bot_commands(application: Application):
    """Настройка команд бота в меню."""
    commands = [
        BotCommand("start", "Начать работу с ботом"),
        BotCommand("profile", "Посмотреть уровень, очки, серию"),
        BotCommand("habits", "Увидеть список ваших привычек"),
        BotCommand("create_habit", "Создать новую привычку (интерактивно)"),
        BotCommand("complete", "Отметить привычку как выполненную"),
        BotCommand("delete_habit", "Удалить привычку"),
        BotCommand("stats", "Посмотреть подробную статистику по привычкам"),
        BotCommand("rewards", "Увидеть список ваших наград (бейджей)"),
        BotCommand("leaderboard", "Посмотреть таблицу лидеров по очкам"),
        BotCommand("cancel", "Отменить текущее действие"),
        BotCommand("help", "Показать это сообщение"),
    ]
    try:
        await application.bot.set_my_commands(commands)
        logger.info("Команды бота успешно установлены")
    except Exception as e:
        logger.error(f"Ошибка при установке команд бота: {e}")


async def start(update, context) -> None:
    """Обработчик команды /start."""
    user = update.effective_user
    if not user:
        await update.message.reply_text("Не удалось получить информацию о пользователе.")
        return

    # Регистрируем или получаем пользователя
    try:
        async for db in get_db_session():
            db_user = await get_or_create_user(
                db=db,
                telegram_id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name,
            )
            
            welcome_message = (
                f"Привет, {user.first_name or user.username or 'пользователь'}! 👋\n"
                "Я бот для отслеживания привычек с элементами геймификации.\n\n"
                "Используйте команды из меню для навигации по боту!\n"
                f"Ваш уровень: {db_user.level} | Очки: {db_user.points}"
            )
            await update.message.reply_text(welcome_message)
            break
            
    except Exception as e:
        logger.error(f"Ошибка при регистрации пользователя {user.id}: {e}")
        await update.message.reply_text(
            "Произошла ошибка при регистрации. Попробуйте позже."
        )


async def update_commands(update, context) -> None:
    """Принудительно обновляет команды бота."""
    try:
        await setup_bot_commands(context.application)
        await update.message.reply_text("✅ Команды бота обновлены!")
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка при обновлении команд: {e}")


async def help_command(update, context) -> None:
    """Обработчик команды /help."""
    help_text = (
        "📋 **Доступные команды:**\n\n"
        "1. /start - Начать работу с ботом\n"
        "2. /profile - Посмотреть уровень, очки, серию\n"
        "3. /habits - Увидеть список ваших привычек\n"
        "4. /create_habit - Создать новую привычку\n"
        "5. /complete - Отметить привычку как выполненную (интерактивно)\n"
        "6. /delete_habit - Удалить привычку\n"
        "7. /stats - Посмотреть подробную статистику по привычкам\n"
        "8. /rewards - Увидеть список ваших наград (бейджей)\n"
        "9. /leaderboard - Посмотреть таблицу лидеров по очкам\n"
        "10. /help - Показать это сообщение\n\n"
        "📅 **Создание привычек:**\n"
        "Используйте команду /create_habit для интерактивного создания привычки.\n\n"
        "**Процесс создания:**\n"
        "1️⃣ Выберите тип расписания (Ежедневно/Еженедельно/Свой график)\n"
        "2️⃣ Введите название привычки\n"
        "3️⃣ Введите описание (необязательно, можно пропустить)\n"
        "4️⃣ Готово! Привычка создана\n\n"
        "**Доступные типы расписания:**\n"
        "• **Ежедневно** - напоминания каждый день в 18:00\n"
        "• **Еженедельно** - напоминания раз в неделю\n"
        "• **Свой график (custom)** - настраиваемое расписание\n\n"
        "**Custom расписание:**\n"
        "Формат: `дни_недели,время,частота`\n"
        "• Дни: пн,вт,ср,чт,пт,сб,вс\n"
        "• Время: HH:MM (например, 18:00)\n"
        "• Частота: каждые N дней (по умолчанию 1)\n\n"
        "**Пример custom:** `пн,ср,пт, 18:00, 1`\n\n"
        "🗑️ **Удаление привычек:**\n"
        "Используйте команду /delete_habit для удаления привычки.\n\n"
        "**Процесс удаления:**\n"
        "1️⃣ Выберите привычку из списка\n"
        "2️⃣ Подтвердите удаление\n"
        "3️⃣ Привычка будет удалена навсегда\n\n"
        "⚠️ **Внимание:** Удаление привычки нельзя отменить!"
    )
    await update.message.reply_text(help_text)


async def setup_scheduler(application: Application):
    """
    Инициализирует и запускает планировщик задач.
    """
    # Настройка команд бота
    await setup_bot_commands(application)
    
    # Запуск планировщика
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

    # Создаем ConversationHandler для создания привычки
    create_habit_conversation = ConversationHandler(
        entry_points=[CommandHandler("create_habit", start_create_habit)],
        states={
            SCHEDULE_TYPE: [
                CallbackQueryHandler(handle_schedule_type, pattern="^schedule_")
            ],
            CUSTOM_SETTINGS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_custom_settings)
            ],
            HABIT_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_habit_name)
            ],
            HABIT_DESCRIPTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_habit_description),
                CommandHandler("skip", handle_habit_description)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel_create_habit)],
        per_message=False,
    )

    # Регистрация обработчиков команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("update_commands", update_commands))
    application.add_handler(CommandHandler("profile", show_profile))
    application.add_handler(CommandHandler("habits", list_habits))
    application.add_handler(create_habit_conversation)  # Новый интерактивный диалог
    application.add_handler(CommandHandler("complete", complete_habit))
    application.add_handler(CommandHandler("delete_habit", delete_habit))
    application.add_handler(CommandHandler("stats", show_stats))
    application.add_handler(CommandHandler("rewards", show_rewards))
    application.add_handler(CommandHandler("leaderboard", show_leaderboard))
    application.add_handler(CommandHandler("test_notifications", test_notifications))
    
    # Добавляем обработчики callback'ов
    application.add_handler(CallbackQueryHandler(handle_complete_callback, pattern="^complete_"))
    application.add_handler(CallbackQueryHandler(handle_delete_callback, pattern="^delete_"))
    application.add_handler(CallbackQueryHandler(handle_delete_confirm_callback, pattern="^(confirm_delete_|cancel_delete)"))

    # Добавление обработчика ошибок
    async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Логирование ошибок, возникающих в обработчиках."""
        logger.error(msg="Вызван исключение в обработчике", exc_info=context.error)

    application.add_error_handler(error_handler)

    # Инициализация планировщика задач и команд бота при запуске приложения
    application.post_init = setup_scheduler

    # Запуск бота в режиме long polling
    logger.info("Запуск бота...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
