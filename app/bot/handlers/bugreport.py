"""
Обработчики для отправки сообщений об ошибках.
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from app.bot.services.bugreport_service import create_bug_report
from app.bot.services.user_service import get_or_create_user
from app.core.database import get_db_session
from app.models.schemas import BugReportCreate
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Состояния для ConversationHandler
WAITING_FOR_TITLE, WAITING_FOR_DESCRIPTION, WAITING_FOR_INCIDENT_TYPE = range(3)

# Типы инцидентов с описаниями
INCIDENT_TYPES = {
    "Critical": "🔴 Полная остановка ключевых процессов, утрата данных",
    "High": "🟠 Частичная недоступность, сбои важных функций",
    "Low": "🟡 Незначительные сбои, нет влияния на бизнес",
    "Feature": "💡 Новая функциональность"
}


async def start_bug_report(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Начать процесс отправки отчета об ошибке.
    """
    try:
        user = update.effective_user
        if not user:
            await update.message.reply_text("❌ Ошибка: не удалось определить пользователя.")
            return ConversationHandler.END

        # Сохраняем информацию о пользователе в контексте
        context.user_data['user_id'] = user.id
        context.user_data['username'] = user.username
        context.user_data['first_name'] = user.first_name
        context.user_data['last_name'] = user.last_name

        await update.message.reply_text(
            "🐛 Отправка сообщения об ошибке\n\n"
            "Пожалуйста, введите краткое описание проблемы (заголовок):\n\n"
            "Пример: 'Бот не отвечает на команды' или 'Ошибка при создании привычки'"
        )
        
        return WAITING_FOR_TITLE
        
    except Exception as e:
        logger.error(f"Ошибка в start_bug_report: {e}")
        await update.message.reply_text("❌ Произошла ошибка. Попробуйте позже.")
        return ConversationHandler.END


async def handle_title(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Обработать введенный заголовок.
    """
    try:
        title = update.message.text.strip()
        
        if len(title) < 5:
            await update.message.reply_text(
                "❌ Заголовок слишком короткий. Пожалуйста, введите более подробное описание (минимум 5 символов):"
            )
            return WAITING_FOR_TITLE
            
        if len(title) > 200:
            await update.message.reply_text(
                "❌ Заголовок слишком длинный. Пожалуйста, сократите до 200 символов:"
            )
            return WAITING_FOR_TITLE
            
        # Сохраняем заголовок
        context.user_data['title'] = title
        
        await update.message.reply_text(
            "📝 Описание проблемы\n\n"
            "Теперь подробно опишите проблему:\n\n"
            "• Что именно произошло?\n"
            "• Какие действия привели к ошибке?\n"
            "• Какой результат вы ожидали?\n"
            "• Есть ли дополнительные детали?\n\n"
            "Максимум 2000 символов."
        )
        
        return WAITING_FOR_DESCRIPTION
        
    except Exception as e:
        logger.error(f"Ошибка в handle_title: {e}")
        await update.message.reply_text("❌ Произошла ошибка. Попробуйте позже.")
        return ConversationHandler.END


async def handle_description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Обработать введенное описание.
    """
    try:
        description = update.message.text.strip()
        
        if len(description) < 10:
            await update.message.reply_text(
                "❌ Описание слишком короткое. Пожалуйста, введите более подробное описание (минимум 10 символов):"
            )
            return WAITING_FOR_DESCRIPTION
            
        if len(description) > 2000:
            await update.message.reply_text(
                "❌ Описание слишком длинное. Пожалуйста, сократите до 2000 символов:"
            )
            return WAITING_FOR_DESCRIPTION
            
        # Сохраняем описание
        context.user_data['description'] = description
        
        # Создаем клавиатуру с типами инцидентов
        keyboard = []
        for incident_type, description_text in INCIDENT_TYPES.items():
            keyboard.append([InlineKeyboardButton(
                f"{incident_type} - {description_text}",
                callback_data=f"incident_type_{incident_type}"
            )])
        
        keyboard.append([InlineKeyboardButton("❌ Отмена", callback_data="cancel_bug_report")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "🔍 Выберите тип инцидента:\n\n"
            "Нажмите на кнопку, которая лучше всего описывает вашу проблему:",
            reply_markup=reply_markup
        )
        
        return WAITING_FOR_INCIDENT_TYPE
        
    except Exception as e:
        logger.error(f"Ошибка в handle_description: {e}")
        await update.message.reply_text("❌ Произошла ошибка. Попробуйте позже.")
        return ConversationHandler.END


async def handle_incident_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Обработать выбранный тип инцидента.
    """
    try:
        query = update.callback_query
        await query.answer()
        
        if query.data == "cancel_bug_report":
            await query.edit_message_text("❌ Отправка отчета об ошибке отменена.")
            return ConversationHandler.END
            
        if query.data.startswith("incident_type_"):
            incident_type = query.data.replace("incident_type_", "")
            
            if incident_type not in INCIDENT_TYPES:
                await query.edit_message_text("❌ Неверный тип инцидента. Попробуйте еще раз.")
                return WAITING_FOR_INCIDENT_TYPE
                
            # Сохраняем тип инцидента
            context.user_data['incident_type'] = incident_type
            
            # Создаем отчет об ошибке
            await create_and_save_bug_report(update, context, incident_type)
            
        return ConversationHandler.END
        
    except Exception as e:
        logger.error(f"Ошибка в handle_incident_type: {e}")
        await update.callback_query.edit_message_text("❌ Произошла ошибка. Попробуйте позже.")
        return ConversationHandler.END


async def create_and_save_bug_report(update: Update, context: ContextTypes.DEFAULT_TYPE, incident_type: str):
    """
    Создать и сохранить отчет об ошибке.
    """
    try:
        query = update.callback_query
        
        # Получаем или создаем пользователя
        async for db in get_db_session():
            user = await get_or_create_user(
                db=db,
                telegram_id=context.user_data['user_id'],
                username=context.user_data['username'],
                first_name=context.user_data['first_name'],
                last_name=context.user_data['last_name']
            )
            
            # Создаем отчет об ошибке напрямую через ORM
            from app.models.database import BugReport
            from datetime import datetime
            
            db_bug_report = BugReport(
                user_id=user.id,
                title=context.user_data['title'],
                description=context.user_data['description'],
                incident_type=incident_type,
                status="New",
                admin_comment=None,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            db.add(db_bug_report)
            await db.commit()
            await db.refresh(db_bug_report)
            
            # Формируем сообщение об успехе
            incident_description = INCIDENT_TYPES[incident_type]
            
            success_message = (
                f"✅ Отчет об ошибке успешно отправлен!\n\n"
                f"📋 ID отчета: {db_bug_report.id}\n"
                f"📝 Заголовок: {db_bug_report.title}\n"
                f"🔍 Тип: {incident_type}\n"
                f"📄 Описание: {incident_description}\n"
                f"📅 Дата: {db_bug_report.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
                f"Спасибо за обратную связь! Мы рассмотрим ваше сообщение в ближайшее время."
            )
            
            await query.edit_message_text(success_message)
            
            # Очищаем данные пользователя
            context.user_data.clear()
            
            logger.info(f"Создан отчет об ошибке {db_bug_report.id} от пользователя {user.telegram_id}")
            break  # Выходим из цикла async for
                
    except Exception as e:
        logger.error(f"Ошибка при создании отчета об ошибке: {e}")
        await query.edit_message_text("❌ Произошла ошибка при сохранении отчета. Попробуйте позже.")


async def cancel_bug_report(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Отменить отправку отчета об ошибке.
    """
    try:
        query = update.callback_query
        if query:
            await query.answer()
            await query.edit_message_text("❌ Отправка отчета об ошибке отменена.")
        else:
            await update.message.reply_text("❌ Отправка отчета об ошибке отменена.")
            
        # Очищаем данные пользователя
        context.user_data.clear()
        
        return ConversationHandler.END
        
    except Exception as e:
        logger.error(f"Ошибка в cancel_bug_report: {e}")
        return ConversationHandler.END


async def show_bug_report_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Показать справку по отправке отчетов об ошибках.
    """
    try:
        help_text = (
            "🐛 Справка по отправке отчетов об ошибках\n\n"
            "Типы инцидентов:\n\n"
            "🔴 Critical - Полная остановка ключевых процессов, утрата данных\n"
            "🟠 High - Частичная недоступность, сбои важных функций\n"
            "🟡 Low - Незначительные сбои, нет влияния на бизнес\n"
            "💡 Feature - Новая функциональность\n\n"
            "Как отправить отчет:\n"
            "1. Используйте команду /send_bugreport\n"
            "2. Введите краткое описание проблемы\n"
            "3. Подробно опишите проблему\n"
            "4. Выберите тип инцидента\n\n"
            "Советы:\n"
            "• Будьте максимально подробными в описании\n"
            "• Укажите шаги для воспроизведения ошибки\n"
            "• Приложите скриншоты, если возможно\n"
            "• Укажите время, когда произошла ошибка"
        )
        
        await update.message.reply_text(help_text)
        
    except Exception as e:
        logger.error(f"Ошибка в show_bug_report_help: {e}")
        await update.message.reply_text("❌ Произошла ошибка при показе справки.")
