"""
Обработчики для интерактивных диалогов с пользователем.
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from app.bot.services.habit_service import create_habit, get_available_schedule_types
from app.bot.services.user_service import get_or_create_user
from app.core.database import get_db_session
import logging

logger = logging.getLogger(__name__)

# Состояния диалога
SCHEDULE_TYPE, HABIT_NAME, HABIT_DESCRIPTION, CUSTOM_SETTINGS = range(4)

# Типы расписания с русскими названиями
SCHEDULE_TYPES = {
    "daily": "Ежедневно",
    "weekly": "Еженедельно", 
    "custom": "Свой график (custom)"
}

# Обратное сопоставление
SCHEDULE_TYPES_REVERSE = {v: k for k, v in SCHEDULE_TYPES.items()}


async def start_create_habit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Начинает диалог создания привычки. Запрашивает тип расписания.
    """
    user = update.effective_user
    if not user:
        await update.message.reply_text("Не удалось получить информацию о пользователе.")
        return ConversationHandler.END

    # Создаем клавиатуру с типами расписания
    keyboard = [
        [InlineKeyboardButton("Ежедневно", callback_data="schedule_daily")],
        [InlineKeyboardButton("Еженедельно", callback_data="schedule_weekly")],
        [InlineKeyboardButton("Свой график (custom)", callback_data="schedule_custom")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "🏗️ **Создание новой привычки**\n\n"
        "Выберите тип расписания:",
        reply_markup=reply_markup
    )

    return SCHEDULE_TYPE


async def handle_schedule_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Обрабатывает выбор типа расписания.
    """
    query = update.callback_query
    await query.answer()

    if query.data.startswith("schedule_"):
        schedule_type = query.data.replace("schedule_", "")
        context.user_data['schedule_type'] = schedule_type
        
        # Если выбран custom, переходим к настройкам custom
        if schedule_type == "custom":
            await query.edit_message_text(
                "📅 **Настройка custom расписания**\n\n"
                "Введите настройки в формате:\n"
                "`дни_недели,время,частота`\n\n"
                "**Примеры:**\n"
                "• `пн,ср,пт, 18:00, 1` - понедельник, среда, пятница в 18:00\n"
                "• `сб,вс, 10:00, 1` - выходные в 10:00\n"
                "• `пн,вт,ср,чт,пт, 09:00, 1` - будни в 9:00\n\n"
                "**Дни недели:** пн, вт, ср, чт, пт, сб, вс\n"
                "**Время:** HH:MM (например, 18:00)\n"
                "**Частота:** каждые N дней (по умолчанию 1)"
            )
            return CUSTOM_SETTINGS
        else:
            # Для daily и weekly переходим к названию
            await query.edit_message_text(
                f"✅ Выбран тип расписания: **{SCHEDULE_TYPES[schedule_type]}**\n\n"
                "📝 Введите название привычки:"
            )
            return HABIT_NAME

    return SCHEDULE_TYPE


async def handle_custom_settings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Обрабатывает настройки custom расписания.
    """
    custom_settings = update.message.text.strip()
    
    # Парсим custom настройки
    parts = custom_settings.split(",")
    if len(parts) < 2:
        await update.message.reply_text(
            "❌ Неверный формат. Используйте: `дни_недели,время,частота`\n"
            "**Пример:** `пн,ср,пт, 18:00, 1`"
        )
        return CUSTOM_SETTINGS
    
    # Сохраняем настройки
    context.user_data['custom_schedule_days'] = parts[0].strip()
    context.user_data['custom_schedule_time'] = parts[1].strip()
    context.user_data['custom_schedule_frequency'] = int(parts[2].strip()) if len(parts) > 2 else 1
    
    await update.message.reply_text(
        f"✅ Настройки custom расписания сохранены:\n"
        f"• Дни: {context.user_data['custom_schedule_days']}\n"
        f"• Время: {context.user_data['custom_schedule_time']}\n"
        f"• Частота: {context.user_data['custom_schedule_frequency']}\n\n"
        "📝 Введите название привычки:"
    )
    
    return HABIT_NAME


async def handle_habit_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Обрабатывает ввод названия привычки.
    """
    habit_name = update.message.text.strip()
    
    if not habit_name:
        await update.message.reply_text("❌ Название привычки не может быть пустым. Попробуйте еще раз:")
        return HABIT_NAME
    
    context.user_data['habit_name'] = habit_name
    
    await update.message.reply_text(
        f"✅ Название: **{habit_name}**\n\n"
        "📄 Введите описание привычки (или отправьте /skip для пропуска):"
    )
    
    return HABIT_DESCRIPTION


async def handle_habit_description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Обрабатывает ввод описания привычки.
    """
    # Проверяем, является ли это командой /skip
    if update.message.text and update.message.text.strip().lower() == "/skip":
        description = ""
    else:
        description = update.message.text.strip() if update.message.text else ""
    
    context.user_data['habit_description'] = description
    
    # Создаем привычку
    try:
        async for db in get_db_session():
            # Убеждаемся, что пользователь зарегистрирован
            db_user = await get_or_create_user(
                db=db,
                telegram_id=update.effective_user.id,
                username=update.effective_user.username,
                first_name=update.effective_user.first_name,
                last_name=update.effective_user.last_name,
            )
            
            # Получаем параметры
            schedule_type = context.user_data['schedule_type']
            habit_name = context.user_data['habit_name']
            habit_description = context.user_data['habit_description']
            
            # Параметры для custom расписания
            custom_schedule_days = context.user_data.get('custom_schedule_days')
            custom_schedule_time = context.user_data.get('custom_schedule_time')
            custom_schedule_frequency = context.user_data.get('custom_schedule_frequency', 1)
            
            # Создаем привычку
            new_habit = await create_habit(
                db=db,
                telegram_id=update.effective_user.id,
                name=habit_name,
                description=habit_description,
                schedule_type=schedule_type,
                custom_schedule_days=custom_schedule_days,
                custom_schedule_time=custom_schedule_time,
                custom_schedule_frequency=custom_schedule_frequency
            )
            
            # Формируем сообщение об успехе
            message = f"🎉 Привычка успешно создана!\n\n"
            message += f"📝 Название: {habit_name}\n"
            if habit_description:
                message += f"📄 Описание: {habit_description}\n"
            message += f"📅 Тип расписания: {SCHEDULE_TYPES[schedule_type]}\n"
            
            # Показываем custom настройки, если они есть
            if schedule_type == "custom":
                if custom_schedule_days:
                    message += f"🗓️ Дни недели: {custom_schedule_days}\n"
                if custom_schedule_time:
                    message += f"⏰ Время напоминания: {custom_schedule_time}\n"
                if custom_schedule_frequency > 1:
                    message += f"🔄 Частота: каждые {custom_schedule_frequency} дня\n"
            
            message += f"⭐ Базовые очки: {new_habit.base_points}\n"
            message += f"🆔 ID привычки: {str(new_habit.id)[:8]}...\n\n"
            message += "Используйте /habits для просмотра всех привычек."
            
            await update.message.reply_text(message)
            break
            
    except Exception as e:
        logger.error(f"Ошибка при создании привычки: {e}")
        await update.message.reply_text(f"❌ Произошла ошибка при создании привычки: {str(e)}")
    
    # Очищаем данные пользователя
    context.user_data.clear()
    
    return ConversationHandler.END


async def cancel_create_habit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Отменяет создание привычки.
    """
    context.user_data.clear()
    await update.message.reply_text("❌ Создание привычки отменено.")
    return ConversationHandler.END
