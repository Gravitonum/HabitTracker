"""
Обработчики для административного интерфейса управления отчетами об ошибках.
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from app.bot.services.async_bugreport_service import (
    get_all_bug_reports_async, get_bug_report_by_id_async, update_bug_report_async,
    get_bug_reports_with_filters_async, get_bug_report_statistics_async,
    delete_bug_report_async, get_bug_reports_by_status_async
)
from app.core.database import get_db_session
from app.core.config import settings
from app.models.schemas import BugReportUpdate
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Состояния для ConversationHandler
WAITING_FOR_COMMENT, WAITING_FOR_STATUS_CHANGE = range(2)


def is_admin(user_id: int) -> bool:
    """
    Проверить, является ли пользователь администратором.
    """
    return user_id == settings.ADMIN_ID

# Статусы отчетов
REPORT_STATUSES = {
    "New": "🆕 Новый",
    "InProgress": "🔄 В работе", 
    "Solved": "✅ Решено",
    "Rejected": "❌ Отклонено"
}

# Типы инцидентов
INCIDENT_TYPES = {
    "Critical": "🔴 Critical",
    "High": "🟠 High", 
    "Low": "🟡 Low",
    "Feature": "💡 Feature"
}


async def admin_bug_reports_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Главное меню администратора для управления отчетами об ошибках.
    """
    try:
        # Проверяем права администратора
        if not is_admin(update.effective_user.id):
            if update.message:
                await update.message.reply_text("❌ У вас нет прав администратора.")
            else:
                await update.callback_query.edit_message_text("❌ У вас нет прав администратора.")
            return

        keyboard = [
            [InlineKeyboardButton("📋 Все отчеты", callback_data="admin_all_reports")],
            [InlineKeyboardButton("🆕 Новые отчеты", callback_data="admin_new_reports")],
            [InlineKeyboardButton("🔄 В работе", callback_data="admin_inprogress_reports")],
            [InlineKeyboardButton("✅ Решенные", callback_data="admin_solved_reports")],
            [InlineKeyboardButton("❌ Отклоненные", callback_data="admin_rejected_reports")],
            [InlineKeyboardButton("📊 Статистика", callback_data="admin_reports_stats")],
            [InlineKeyboardButton("🔍 Поиск", callback_data="admin_search_reports")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.message:
            await update.message.reply_text(
                "🔧 Административная панель - Отчеты об ошибках\n\n"
                "Выберите действие:",
                reply_markup=reply_markup
            )
        else:
            await update.callback_query.edit_message_text(
                "🔧 Административная панель - Отчеты об ошибках\n\n"
                "Выберите действие:",
                reply_markup=reply_markup
            )
        
    except Exception as e:
        logger.error(f"Ошибка в admin_bug_reports_menu: {e}")
        if update.message:
            await update.message.reply_text("❌ Произошла ошибка. Попробуйте позже.")
        else:
            await update.callback_query.edit_message_text("❌ Произошла ошибка. Попробуйте позже.")


async def handle_admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработать callback от административных кнопок.
    """
    try:
        query = update.callback_query
        await query.answer()
        
        # Проверяем права администратора
        if not is_admin(update.effective_user.id):
            await query.edit_message_text("❌ У вас нет прав администратора.")
            return
        
        if query.data == "admin_all_reports":
            await show_all_reports(update, context)
        elif query.data == "admin_new_reports":
            context.user_data['current_filter'] = 'status'
            context.user_data['current_status'] = 'New'
            await show_reports_by_status(update, context, "New")
        elif query.data == "admin_inprogress_reports":
            context.user_data['current_filter'] = 'status'
            context.user_data['current_status'] = 'InProgress'
            await show_reports_by_status(update, context, "InProgress")
        elif query.data == "admin_solved_reports":
            context.user_data['current_filter'] = 'status'
            context.user_data['current_status'] = 'Solved'
            await show_reports_by_status(update, context, "Solved")
        elif query.data == "admin_rejected_reports":
            context.user_data['current_filter'] = 'status'
            context.user_data['current_status'] = 'Rejected'
            await show_reports_by_status(update, context, "Rejected")
        elif query.data == "admin_reports_stats":
            await show_reports_statistics(update, context)
        elif query.data == "admin_search_reports":
            await start_search_reports(update, context)
        elif query.data.startswith("view_report_"):
            report_id = query.data.replace("view_report_", "")
            await show_report_details(update, context, report_id)
        elif query.data.startswith("change_status_"):
            report_id = query.data.replace("change_status_", "")
            await start_status_change(update, context, report_id)
        elif query.data.startswith("set_status_"):
            await handle_status_change(update, context)
        elif query.data.startswith("add_comment_"):
            report_id = query.data.replace("add_comment_", "")
            await start_add_comment(update, context, report_id)
        elif query.data.startswith("delete_report_"):
            report_id = query.data.replace("delete_report_", "")
            await delete_report(update, context, report_id)
        elif query.data.startswith("confirm_delete_report_"):
            report_id = query.data.replace("confirm_delete_report_", "")
            await confirm_delete_report(update, context, report_id)
        elif query.data == "back_to_admin_menu":
            await admin_bug_reports_menu(update, context)
            
    except Exception as e:
        logger.error(f"Ошибка в handle_admin_callback: {e}")
        await query.edit_message_text("❌ Произошла ошибка. Попробуйте позже.")


async def show_all_reports(update: Update, context: ContextTypes.DEFAULT_TYPE, page: int = 0):
    """
    Показать все отчеты с пагинацией.
    """
    try:
        query = update.callback_query
        skip = page * 10
        limit = 10
        
        async for db in get_db_session():
            reports = await get_all_bug_reports_async(db, skip=skip, limit=limit)
            
            if not reports:
                await query.edit_message_text(
                    "📋 Все отчеты об ошибках\n\n"
                    "Отчеты не найдены.",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 Назад", callback_data="back_to_admin_menu")
                    ]])
                )
                return
                
            # Формируем список отчетов
            text = f"📋 Все отчеты об ошибках (страница {page + 1})\n\n"
            
            keyboard = []
            for i, report in enumerate(reports, 1):
                status_emoji = REPORT_STATUSES.get(report.status, "❓")
                incident_emoji = INCIDENT_TYPES.get(report.incident_type, "❓")
                
                text += f"{i}. {status_emoji} {incident_emoji} {report.title}\n"
                text += f"   ID: {str(report.id)[:8]}... | {report.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
                
                keyboard.append([InlineKeyboardButton(
                    f"📄 {report.title[:30]}...",
                    callback_data=f"view_report_{report.id}"
                )])
            
            # Кнопки пагинации
            nav_buttons = []
            if page > 0:
                nav_buttons.append(InlineKeyboardButton("⬅️ Назад", callback_data=f"admin_all_reports_page_{page-1}"))
            if len(reports) == limit:
                nav_buttons.append(InlineKeyboardButton("➡️ Вперед", callback_data=f"admin_all_reports_page_{page+1}"))
            
            if nav_buttons:
                keyboard.append(nav_buttons)
                
            keyboard.append([InlineKeyboardButton("🔙 Назад в меню", callback_data="back_to_admin_menu")])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(text, reply_markup=reply_markup, )
            
            break  # Выходим из цикла async for
            
    except Exception as e:
        logger.error(f"Ошибка в show_all_reports: {e}")
        await query.edit_message_text("❌ Произошла ошибка при загрузке отчетов.")


async def show_reports_by_status(update: Update, context: ContextTypes.DEFAULT_TYPE, status: str):
    """
    Показать отчеты по статусу.
    """
    try:
        query = update.callback_query
        
        async for db in get_db_session():
            reports = await get_bug_reports_by_status_async(db, status, skip=0, limit=50)
            
            if not reports:
                status_name = REPORT_STATUSES.get(status, status)
                await query.edit_message_text(
                    f"📋 Отчеты со статусом: {status_name}\n\n"
                    "Отчеты не найдены.",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 Назад", callback_data="back_to_admin_menu")
                    ]])
                )
                return
                
            # Формируем список отчетов
            status_name = REPORT_STATUSES.get(status, status)
            text = f"📋 Отчеты со статусом: {status_name}\n\n"
            
            keyboard = []
            for i, report in enumerate(reports, 1):
                incident_emoji = INCIDENT_TYPES.get(report.incident_type, "❓")
                
                text += f"{i}. {incident_emoji} {report.title}\n"
                text += f"   ID: {str(report.id)[:8]}... | {report.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
                
                keyboard.append([InlineKeyboardButton(
                    f"📄 {report.title[:30]}...",
                    callback_data=f"view_report_{report.id}"
                )])
            
            keyboard.append([InlineKeyboardButton("🔙 Назад в меню", callback_data="back_to_admin_menu")])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(text, reply_markup=reply_markup, )
            
            break  # Выходим из цикла async for
            
    except Exception as e:
        logger.error(f"Ошибка в show_reports_by_status: {e}")
        await query.edit_message_text("❌ Произошла ошибка при загрузке отчетов.")


async def show_report_details(update: Update, context: ContextTypes.DEFAULT_TYPE, report_id: str):
    """
    Показать детали отчета об ошибке.
    """
    try:
        query = update.callback_query
        
        async for db in get_db_session():
            report = await get_bug_report_by_id_async(db, report_id)
            
            if not report:
                await query.edit_message_text(
                    "❌ Отчет не найден.",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 Назад", callback_data="back_to_admin_menu")
                    ]])
                )
                return
                
            # Формируем детальную информацию
            status_emoji = REPORT_STATUSES.get(report.status, "❓")
            incident_emoji = INCIDENT_TYPES.get(report.incident_type, "❓")
            
            text = f"📄 Детали отчета об ошибке\n\n"
            text += f"🆔 ID: {report.id}\n"
            text += f"📝 Заголовок: {report.title}\n"
            text += f"🔍 Тип: {incident_emoji} {report.incident_type}\n"
            text += f"📊 Статус: {status_emoji} {report.status}\n"
            text += f"📅 Создан: {report.created_at.strftime('%d.%m.%Y %H:%M')}\n"
            text += f"🔄 Обновлен: {report.updated_at.strftime('%d.%m.%Y %H:%M') if report.updated_at else 'Не обновлялся'}\n\n"
            text += f"📋 Описание:\n{report.description}\n\n"
            
            if report.admin_comment:
                text += f"💬 Комментарий администратора:\n{report.admin_comment}\n\n"
            
            # Определяем, к какому списку возвращаться
            current_filter = context.user_data.get('current_filter', 'all')
            if current_filter == 'status':
                current_status = context.user_data.get('current_status', 'New')
                back_callback = f"admin_{current_status.lower()}_reports"
            else:
                back_callback = "admin_all_reports"
            
            # Кнопки управления
            keyboard = [
                [InlineKeyboardButton("🔄 Изменить статус", callback_data=f"change_status_{str(report.id)}")],
                [InlineKeyboardButton("💬 Добавить комментарий", callback_data=f"add_comment_{str(report.id)}")],
                [InlineKeyboardButton("🗑️ Удалить", callback_data=f"delete_report_{str(report.id)}")],
                [InlineKeyboardButton("🔙 Назад к списку", callback_data=back_callback)]
            ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(text, reply_markup=reply_markup, )
            
            break  # Выходим из цикла async for
            
    except Exception as e:
        logger.error(f"Ошибка в show_report_details: {e}")
        await query.edit_message_text("❌ Произошла ошибка при загрузке отчета.")


async def start_status_change(update: Update, context: ContextTypes.DEFAULT_TYPE, report_id: str):
    """
    Начать процесс изменения статуса отчета.
    """
    try:
        query = update.callback_query
        
        # Сохраняем ID отчета в контексте
        context.user_data['report_id'] = report_id
        
        keyboard = []
        for status, status_name in REPORT_STATUSES.items():
            keyboard.append([InlineKeyboardButton(
                status_name,
                callback_data=f"set_status_{status}"
            )])
        
        keyboard.append([InlineKeyboardButton("❌ Отмена", callback_data=f"view_report_{report_id}")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "🔄 Изменение статуса отчета\n\n"
            "Выберите новый статус:",
            reply_markup=reply_markup
        )
        
    except Exception as e:
        logger.error(f"Ошибка в start_status_change: {e}")
        await query.edit_message_text("❌ Произошла ошибка.")


async def handle_status_change(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработать изменение статуса отчета.
    """
    try:
        query = update.callback_query
        await query.answer()
        
        if query.data.startswith("set_status_"):
            new_status = query.data.replace("set_status_", "")
            report_id = context.user_data.get('report_id')
            
            if not report_id:
                await query.edit_message_text("❌ Ошибка: ID отчета не найден.")
                return
                
            async for db in get_db_session():
                update_data = BugReportUpdate(status=new_status)
                updated_report = await update_bug_report_async(db, report_id, update_data)
                
                if updated_report:
                    status_name = REPORT_STATUSES.get(new_status, new_status)
                    
                    # Определяем, к какому списку возвращаться
                    current_filter = context.user_data.get('current_filter', 'all')
                    if current_filter == 'status':
                        current_status = context.user_data.get('current_status', 'New')
                        back_callback = f"admin_{current_status.lower()}_reports"
                    else:
                        back_callback = "admin_all_reports"
                    
                    await query.edit_message_text(
                        f"✅ Статус отчета успешно изменен на: {status_name}",
                        reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton("📄 Просмотреть отчет", callback_data=f"view_report_{report_id}")],
                            [InlineKeyboardButton("📋 Назад к списку", callback_data=back_callback)]
                        ])
                    )
                else:
                    await query.edit_message_text("❌ Ошибка при изменении статуса.")
                    
                # Очищаем данные из контекста
                context.user_data.pop('report_id', None)
                
                break  # Выходим из цикла async for
            
    except Exception as e:
        logger.error(f"Ошибка в handle_status_change: {e}")
        await query.edit_message_text("❌ Произошла ошибка при изменении статуса.")


async def start_add_comment(update: Update, context: ContextTypes.DEFAULT_TYPE, report_id: str):
    """
    Начать процесс добавления комментария к отчету.
    """
    try:
        query = update.callback_query
        
        # Сохраняем ID отчета в контексте
        context.user_data['report_id'] = report_id
        
        await query.edit_message_text(
            "💬 Добавление комментария\n\n"
            "Введите комментарий для отчета (максимум 1000 символов):\n\n"
            "Используйте /cancel для отмены."
        )
        
        return WAITING_FOR_COMMENT
        
    except Exception as e:
        logger.error(f"Ошибка в start_add_comment: {e}")
        await query.edit_message_text("❌ Произошла ошибка.")


async def handle_comment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Обработать введенный комментарий.
    """
    try:
        comment = update.message.text.strip()
        report_id = context.user_data.get('report_id')
        
        if not report_id:
            await update.message.reply_text("❌ Ошибка: ID отчета не найден.")
            return ConversationHandler.END
            
        if len(comment) > 1000:
            await update.message.reply_text(
                "❌ Комментарий слишком длинный. Максимум 1000 символов. Попробуйте еще раз:"
            )
            return WAITING_FOR_COMMENT
            
        async for db in get_db_session():
            update_data = BugReportUpdate(admin_comment=comment)
            updated_report = await update_bug_report_async(db, report_id, update_data)
            
            if updated_report:
                await update.message.reply_text(
                    f"✅ Комментарий успешно добавлен к отчету {str(report_id)[:8]}...",
                )
            else:
                await update.message.reply_text("❌ Ошибка при добавлении комментария.")
                
            # Очищаем данные из контекста
            context.user_data.pop('report_id', None)
            
            break  # Выходим из цикла async for
        
        return ConversationHandler.END
        
    except Exception as e:
        logger.error(f"Ошибка в handle_comment: {e}")
        await update.message.reply_text("❌ Произошла ошибка при добавлении комментария.")
        return ConversationHandler.END


async def delete_report(update: Update, context: ContextTypes.DEFAULT_TYPE, report_id: str):
    """
    Удалить отчет об ошибке.
    """
    try:
        query = update.callback_query
        
        # Подтверждение удаления
        keyboard = [
            [InlineKeyboardButton("✅ Да, удалить", callback_data=f"confirm_delete_report_{report_id}")],
            [InlineKeyboardButton("❌ Отмена", callback_data=f"view_report_{report_id}")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"⚠️ Подтверждение удаления\n\n"
            f"Вы уверены, что хотите удалить отчет {str(report_id)[:8]}...?\n\n"
            f"Это действие нельзя отменить!",
            reply_markup=reply_markup,
        )
        
    except Exception as e:
        logger.error(f"Ошибка в delete_report: {e}")
        await query.edit_message_text("❌ Произошла ошибка.")


async def confirm_delete_report(update: Update, context: ContextTypes.DEFAULT_TYPE, report_id: str):
    """
    Подтвердить удаление отчета.
    """
    try:
        query = update.callback_query
        await query.answer()
        
        async for db in get_db_session():
            success = await delete_bug_report_async(db, report_id)
            
            if success:
                await query.edit_message_text(
                    f"✅ Отчет {str(report_id)[:8]}... успешно удален.",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 Назад к списку", callback_data="admin_all_reports")
                    ]]),
                )
            else:
                await query.edit_message_text(
                    "❌ Ошибка при удалении отчета.",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 Назад", callback_data=f"view_report_{report_id}")
                    ]])
                )
            
            break  # Выходим из цикла async for
                
    except Exception as e:
        logger.error(f"Ошибка в confirm_delete_report: {e}")
        await query.edit_message_text("❌ Произошла ошибка при удалении отчета.")


async def show_reports_statistics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Показать статистику по отчетам об ошибках.
    """
    try:
        query = update.callback_query
        
        async for db in get_db_session():
            stats = await get_bug_report_statistics_async(db)
            
            text = "📊 Статистика отчетов об ошибках\n\n"
            text += f"📈 Всего отчетов: {stats['total']}\n"
            text += f"🕐 За последние 24 часа: {stats['recent_24h']}\n\n"
            
            text += "📊 По статусам:\n"
            for status, count in stats['by_status'].items():
                status_emoji = REPORT_STATUSES.get(status, "❓")
                text += f"  {status_emoji} {status}: {count}\n"
                
            text += "\n🔍 По типам инцидентов:\n"
            for incident_type, count in stats['by_incident_type'].items():
                incident_emoji = INCIDENT_TYPES.get(incident_type, "❓")
                text += f"  {incident_emoji} {incident_type}: {count}\n"
            
            keyboard = [[InlineKeyboardButton("🔙 Назад в меню", callback_data="back_to_admin_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(text, reply_markup=reply_markup)
            
            break  # Выходим из цикла async for
            
    except Exception as e:
        logger.error(f"Ошибка в show_reports_statistics: {e}")
        await query.edit_message_text("❌ Произошла ошибка при загрузке статистики.")


async def start_search_reports(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Начать поиск отчетов.
    """
    try:
        query = update.callback_query
        
        await query.edit_message_text(
            "🔍 Поиск отчетов об ошибках\n\n"
            "Введите поисковый запрос (поиск по заголовку, описанию и комментариям):\n\n"
            "Используйте /cancel для отмены."
        )
        
        return WAITING_FOR_COMMENT  # Переиспользуем состояние
        
    except Exception as e:
        logger.error(f"Ошибка в start_search_reports: {e}")
        await query.edit_message_text("❌ Произошла ошибка.")


async def handle_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Обработать поисковый запрос.
    """
    try:
        search_query = update.message.text.strip()
        
        async for db in get_db_session():
            reports = await get_bug_reports_with_filters_async(db, search_query=search_query, limit=20)
            
            if not reports:
                await update.message.reply_text(
                    f"🔍 Результаты поиска: '{search_query}'\n\n"
                    "Отчеты не найдены.",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 Назад", callback_data="back_to_admin_menu")
                    ]])
                )
                return ConversationHandler.END
                
            # Формируем результаты поиска
            text = f"🔍 Результаты поиска: '{search_query}'\n\n"
            
            keyboard = []
            for i, report in enumerate(reports, 1):
                status_emoji = REPORT_STATUSES.get(report.status, "❓")
                incident_emoji = INCIDENT_TYPES.get(report.incident_type, "❓")
                
                text += f"{i}. {status_emoji} {incident_emoji} {report.title}\n"
                text += f"   ID: {str(report.id)[:8]}... | {report.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
                
                keyboard.append([InlineKeyboardButton(
                    f"📄 {report.title[:30]}...",
                    callback_data=f"view_report_{report.id}"
                )])
            
            keyboard.append([InlineKeyboardButton("🔙 Назад в меню", callback_data="back_to_admin_menu")])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(text, reply_markup=reply_markup, )
            
            break  # Выходим из цикла async for
        
        return ConversationHandler.END
        
    except Exception as e:
        logger.error(f"Ошибка в handle_search: {e}")
        await update.message.reply_text("❌ Произошла ошибка при поиске.")
        return ConversationHandler.END


async def cancel_admin_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Отменить административное действие.
    """
    try:
        await update.message.reply_text("❌ Действие отменено.")
        # Очищаем данные из контекста
        context.user_data.clear()
        return ConversationHandler.END
        
    except Exception as e:
        logger.error(f"Ошибка в cancel_admin_action: {e}")
        return ConversationHandler.END
