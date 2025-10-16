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
    get_all_completions_for_habit,
    get_available_schedule_types,
    calculate_current_streak,
)
from app.models.database import ScheduleType, HabitCompletion, Habit
from app.bot.services.reward_service import award_points_and_rewards
from app.bot.services.user_service import get_or_create_user
from app.utils.points_calculator import calculate_total_points_for_completion
from app.utils.streak_calculator import update_streak_increment
from app.core.database import get_db_session
from datetime import date
from sqlalchemy import select
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
            
            # Получаем привычки пользователя
            habits = await get_user_habits(db, telegram_id)
            
            if not habits:
                message = f"У вас пока нет привычек, {user.first_name or user.username or 'пользователь'}!\n"
                message += "Создайте первую привычку командой /create_habit"
                await _send_reply(update, message)
                break
            
            # Получаем все типы расписания для сопоставления
            from sqlalchemy import select
            schedule_types_result = await db.execute(select(ScheduleType))
            schedule_types = {st.id: st.name for st in schedule_types_result.scalars().all()}
            
            # Словарь для перевода типов расписания на русский
            schedule_type_names = {
                "daily": "Ежедневно",
                "weekly": "Еженедельно",
                "custom": "Свой график"
            }
            
            message = f"📋 Список ваших привычек, {user.first_name or user.username or 'пользователь'}:\n\n"
            
            # Получаем информацию о выполнении сегодня для каждой привычки
            from datetime import date
            for i, habit in enumerate(habits, 1):
                status = "✅" if habit.is_active else "❌"
                schedule_type_name = schedule_type_names.get(schedule_types.get(habit.schedule_type_id), "Неизвестно")
                
                # Проверяем, выполнена ли привычка сегодня
                today_completion = await db.execute(
                    select(HabitCompletion)
                    .where(HabitCompletion.habit_id == habit.id)
                    .where(HabitCompletion.completion_date == date.today())
                    .where(HabitCompletion.is_completed == True)
                )
                is_completed_today = today_completion.scalar_one_or_none() is not None
                today_status = "✅ Выполнено сегодня" if is_completed_today else "❌ Не выполнено сегодня"
                
                # Вычисляем текущую серию
                current_streak = await calculate_current_streak(db, habit.id)
                streak_text = f"{current_streak} дней подряд" if current_streak > 0 else "нет серии"
                
                message += f"{i}. {status} {habit.name}\n"
                if habit.description:
                    message += f"   📄 {habit.description}\n"
                message += f"   📅 {schedule_type_name}"
                
                # Показываем custom настройки, если они есть
                if schedule_types.get(habit.schedule_type_id) == "custom":
                    if habit.custom_schedule_days:
                        message += f" ({habit.custom_schedule_days}"
                    if habit.custom_schedule_time:
                        message += f", {habit.custom_schedule_time}"
                    if habit.custom_schedule_frequency and habit.custom_schedule_frequency > 1:
                        message += f", каждые {habit.custom_schedule_frequency} дня"
                    if habit.custom_schedule_days:
                        message += ")"
                
                message += f"\n   🔥 Серия: {streak_text}\n"
                message += f"   {today_status}\n"
                message += f"   ⭐ {habit.base_points} очков\n\n"
            
            message += "\nЧтобы отметить привычку, используйте /complete <номер>"
            await _send_reply(update, message)
            break
            
    except Exception as e:
        logger.error(f"Ошибка при получении привычек для пользователя {telegram_id}: {e}")
        await _send_reply(update, "Произошла ошибка при получении списка привычек.")


async def create_habit_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Команда для создания новой привычки (старый формат - для совместимости).
    Рекомендуется использовать интерактивный диалог.
    """
    user = update.effective_user
    if not user:
        await _send_reply(update, "Не удалось получить информацию о пользователе.")
        return

    if not context.args:
        await _send_reply(
            update,
            "🏗️ **Создание привычки**\n\n"
            "Рекомендуется использовать интерактивный режим!\n"
            "Просто отправьте команду /create_habit без параметров.\n\n"
            "**Старый формат (для совместимости):**\n"
            "`/create_habit Название - Описание - Тип_расписания`\n\n"
            "**Примеры:**\n"
            "• `/create_habit Пить воду - Ежедневно пить 2 литра воды - daily`\n"
            "• `/create_habit Тренировка - 3 раза в неделю - weekly`\n"
            "• `/create_habit Чтение - По выходным - custom - пн,ср,пт, 18:00, 1`\n\n"
            "**Доступные типы:** daily, weekly, custom"
        )
        return

    command_text = " ".join(context.args)
    
    # Парсим команду: название - описание - тип_расписания - custom_настройки
    parts = command_text.split(" - ")
    if len(parts) < 2:
        await _send_reply(update, "Неверный формат команды. Используйте: название - описание - тип_расписания")
        return
    
    name = parts[0].strip()
    description = parts[1].strip()
    schedule_type = parts[2].strip().lower() if len(parts) > 2 else "daily"
    
    # Параметры для custom расписания
    custom_schedule_days = None
    custom_schedule_time = None
    custom_schedule_frequency = 1
    
    if schedule_type == "custom" and len(parts) > 3:
        # Парсим custom настройки: дни_недели,время,частота
        custom_settings = parts[3].strip()
        if custom_settings:
            custom_parts = custom_settings.split(",")
            if len(custom_parts) >= 1:
                custom_schedule_days = custom_parts[0].strip()
            if len(custom_parts) >= 2:
                custom_schedule_time = custom_parts[1].strip()
            if len(custom_parts) >= 3:
                try:
                    custom_schedule_frequency = int(custom_parts[2].strip())
                except ValueError:
                    custom_schedule_frequency = 1

    if not name:
        await _send_reply(update, "Название привычки не может быть пустым.")
        return

    # Проверяем валидность типа расписания
    valid_schedule_types = ["daily", "weekly", "custom"]
    if schedule_type not in valid_schedule_types:
        await _send_reply(
            update, 
            f"Неверный тип расписания '{schedule_type}'. Доступные типы: {', '.join(valid_schedule_types)}"
        )
        return

    try:
        async for db in get_db_session():
            # Убеждаемся, что пользователь зарегистрирован
            db_user = await get_or_create_user(
                db=db,
                telegram_id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name,
            )
            
            # Создаем привычку
            new_habit = await create_habit(
                db=db, 
                telegram_id=user.id, 
                name=name, 
                description=description,
                schedule_type=schedule_type,
                custom_schedule_days=custom_schedule_days,
                custom_schedule_time=custom_schedule_time,
                custom_schedule_frequency=custom_schedule_frequency,
                timezone="Europe/Moscow"  # По умолчанию московское время
            )

            # Переводим тип расписания на русский
            schedule_type_names = {
                "daily": "ежедневно",
                "weekly": "еженедельно", 
                "custom": "настраиваемое"
            }

            message = f"Привычка '{name}' успешно создана! ✅\n"
            if description:
                message += f"Описание: {description}\n"
            message += f"Тип расписания: {schedule_type_names[schedule_type]}\n"
            
            # Показываем custom настройки, если они есть
            if schedule_type == "custom":
                if custom_schedule_days:
                    message += f"Дни недели: {custom_schedule_days}\n"
                if custom_schedule_time:
                    message += f"Время напоминания: {custom_schedule_time}\n"
                if custom_schedule_frequency > 1:
                    message += f"Частота: каждые {custom_schedule_frequency} дня\n"
            
            message += f"Базовые очки: {new_habit.base_points}\n"
            message += f"ID привычки: {str(new_habit.id)[:8]}..."
            
            await _send_reply(update, message)
            break
            
    except Exception as e:
        logger.error(f"Ошибка при создании привычки для пользователя {user.id}: {e}")
        await _send_reply(update, f"Произошла ошибка при создании привычки: {str(e)}")


async def complete_habit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Показывает список привычек для выбора и отмечает выбранную как выполненную.
    """
    user = update.effective_user
    if not user:
        await _send_reply(update, "Не удалось получить информацию о пользователе.")
        return

    try:
        async for db in get_db_session():
            # Убеждаемся, что пользователь зарегистрирован
            db_user = await get_or_create_user(
                db=db,
                telegram_id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name,
            )
            
            # Получаем привычки пользователя
            habits = await get_user_habits(db, user.id)
            
            if not habits:
                await _send_reply(update, "У вас пока нет привычек. Создайте первую привычку командой /create_habit")
                break
            
            # Получаем все типы расписания для сопоставления
            schedule_types_result = await db.execute(select(ScheduleType))
            schedule_types = {st.id: st.name for st in schedule_types_result.scalars().all()}
            
            # Словарь для перевода типов расписания на русский
            schedule_type_names = {
                "daily": "Ежедневно",
                "weekly": "Еженедельно",
                "custom": "Свой график"
            }
            
            # Создаем клавиатуру с привычками
            from telegram import InlineKeyboardButton, InlineKeyboardMarkup
            keyboard = []
            
            message = f"📋 Выберите привычку для отметки выполнения:\n\n"
            
            for i, habit in enumerate(habits, 1):
                status = "✅" if habit.is_active else "❌"
                schedule_type_name = schedule_type_names.get(schedule_types.get(habit.schedule_type_id), "Неизвестно")
                
                # Проверяем, выполнена ли привычка сегодня
                today_completion = await db.execute(
                    select(HabitCompletion)
                    .where(HabitCompletion.habit_id == habit.id)
                    .where(HabitCompletion.completion_date == date.today())
                    .where(HabitCompletion.is_completed == True)
                )
                is_completed_today = today_completion.scalar_one_or_none() is not None
                today_status = "✅ Выполнено" if is_completed_today else "❌ Не выполнено"
                
                # Вычисляем текущую серию
                current_streak = await calculate_current_streak(db, habit.id)
                streak_text = f"{current_streak} дней" if current_streak > 0 else "нет серии"
                
                message += f"{i}. {status} {habit.name}\n"
                message += f"   📅 {schedule_type_name} | {today_status} | 🔥 {streak_text}\n\n"
                
                # Добавляем кнопку для каждой привычки
                button_text = f"{i}. {habit.name}"
                if is_completed_today:
                    button_text += " ✅"
                keyboard.append([InlineKeyboardButton(button_text, callback_data=f"complete_{habit.id}")])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await _send_reply(update, message)
            await update.message.reply_text("Нажмите на привычку, которую хотите отметить как выполненную:", reply_markup=reply_markup)
            break
            
    except Exception as e:
        logger.error(f"Ошибка при получении привычек для пользователя {user.id}: {e}")
        await _send_reply(update, "Произошла ошибка при получении списка привычек.")


async def handle_complete_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обрабатывает выбор привычки для отметки выполнения.
    """
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith("complete_"):
        habit_id_str = query.data.replace("complete_", "")
        
        try:
            # Преобразуем строку в UUID
            import uuid
            habit_id = uuid.UUID(habit_id_str)
            
            async for db in get_db_session():
                # Убеждаемся, что пользователь зарегистрирован и получаем его UUID
                db_user = await get_or_create_user(
                    db=db,
                    telegram_id=query.from_user.id,
                    username=query.from_user.username,
                    first_name=query.from_user.first_name,
                    last_name=query.from_user.last_name,
                )
                
                # Получаем привычку по ID
                habit_result = await db.execute(
                    select(Habit).where(Habit.id == habit_id)
                )
                habit = habit_result.scalar_one_or_none()
                
                if not habit:
                    await query.edit_message_text("❌ Привычка не найдена.")
                    return
                
                # Проверяем, не выполнена ли уже привычка сегодня
                today_completion = await db.execute(
                    select(HabitCompletion)
                    .where(HabitCompletion.habit_id == habit.id)
                    .where(HabitCompletion.completion_date == date.today())
                    .where(HabitCompletion.is_completed == True)
                )
                existing_completion = today_completion.scalar_one_or_none()
                
                if existing_completion:
                    await query.edit_message_text(f"❌ Привычка '{habit.name}' уже отмечена как выполненная сегодня!")
                    return
                
                # Получаем все отметки для этой привычки
                all_completions = await get_all_completions_for_habit(db, habit.id)
                
                # Рассчитываем streak_increment
                streak_val = update_streak_increment(habit.id, db_user.id, date.today(), all_completions)
                
                # Отмечаем выполнение
                completion = await mark_habit_completed(db, habit.id, db_user.id, date.today(), streak_val)
                
                # Рассчитываем и начисляем очки
                points_earned = calculate_total_points_for_completion(habit, streak_val)
                await award_points_and_rewards(db, query.from_user.id, points_earned, streak_val)
                
                # Формируем сообщение об успехе
                message = f"🎉 Привычка '{habit.name}' отмечена как выполненная!\n\n"
                message += f"⭐ Получено очков: {points_earned}\n"
                if streak_val > 0:
                    message += f"🔥 Серия: {streak_val} дней подряд\n"
                message += f"📅 Дата: {date.today().strftime('%d.%m.%Y')}\n\n"
                message += "Используйте /habits для просмотра обновленного списка."
                
                await query.edit_message_text(message)
                break
                
        except Exception as e:
            logger.error(f"Ошибка при отметке привычки: {e}")
            await query.edit_message_text(f"❌ Произошла ошибка при отметке привычки: {str(e)}")


async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Показывает статистику по привычкам пользователя.
    """
    user = update.effective_user
    if not user:
        await _send_reply(update, "Не удалось получить информацию о пользователе.")
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
            
            # Получаем статистику
            stats = await get_user_statistics(db, telegram_id)
            
            if "error" in stats:
                await _send_reply(update, f"Ошибка: {stats['error']}")
                break
            
            if stats["total_habits"] == 0:
                message = f"У вас пока нет привычек, {user.first_name or user.username or 'пользователь'}!\n"
                message += "Создайте первую привычку командой /create_habit"
                await _send_reply(update, message)
                break
            
            # Получаем все типы расписания для сопоставления
            from sqlalchemy import select
            schedule_types_result = await db.execute(select(ScheduleType))
            schedule_types = {st.id: st.name for st in schedule_types_result.scalars().all()}
            
            # Словарь для перевода типов расписания на русский
            schedule_type_names = {
                "daily": "Ежедневно",
                "weekly": "Еженедельно",
                "custom": "Свой график"
            }
            
            # Формируем сообщение со статистикой
            message = f"📊 Статистика привычек для {user.first_name or user.username or 'пользователь'}:\n\n"
            
            # Статистика по каждой привычке
            for habit_stat in stats["habits"]:
                habit = habit_stat["habit"]
                status_icon = "✅" if habit_stat["completed_today"] else "❌"
                streak_text = f"{habit_stat['current_streak']} дней подряд" if habit_stat['current_streak'] > 0 else "нет серии"
                schedule_type_name = schedule_type_names.get(schedule_types.get(habit.schedule_type_id), "Неизвестно")
                
                message += f"{status_icon} {habit.name}\n"
                message += f"   📅 {schedule_type_name}\n"
                message += f"   🔥 Серия: {streak_text}\n"
                message += f"   📊 Выполнено за неделю: {habit_stat['week_completions']}/7 дней\n"
                message += f"   📈 Всего выполнений: {habit_stat['total_completions']}\n\n"
            
            # Общая статистика
            message += f"📈 Общая статистика:\n"
            message += f"   Выполнено сегодня: {stats['completed_today']}/{stats['total_habits']} привычек\n"
            message += f"   Общий прогресс: {stats['overall_progress']:.1f}%\n"
            message += f"   Всего выполнений: {stats['total_completions']}"
            
            await _send_reply(update, message)
            break
            
    except Exception as e:
        logger.error(f"Ошибка при получении статистики для пользователя {telegram_id}: {e}")
        await _send_reply(update, "Произошла ошибка при получении статистики.")


async def delete_habit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Показывает список привычек для удаления.
    """
    user = update.effective_user
    if not user:
        await _send_reply(update, "Не удалось получить информацию о пользователе.")
        return

    try:
        async for db in get_db_session():
            # Убеждаемся, что пользователь зарегистрирован
            db_user = await get_or_create_user(
                db=db,
                telegram_id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name,
            )
            
            # Получаем привычки пользователя
            habits = await get_user_habits(db, user.id)
            
            if not habits:
                await _send_reply(update, "У вас пока нет привычек для удаления.")
                break
            
            # Получаем все типы расписания для сопоставления
            schedule_types_result = await db.execute(select(ScheduleType))
            schedule_types = {st.id: st.name for st in schedule_types_result.scalars().all()}
            
            # Словарь для перевода типов расписания на русский
            schedule_type_names = {
                "daily": "Ежедневно",
                "weekly": "Еженедельно",
                "custom": "Свой график"
            }
            
            # Создаем клавиатуру с привычками
            from telegram import InlineKeyboardButton, InlineKeyboardMarkup
            keyboard = []
            
            message = f"🗑️ Выберите привычку для удаления:\n\n"
            
            for i, habit in enumerate(habits, 1):
                status = "✅" if habit.is_active else "❌"
                schedule_type_name = schedule_type_names.get(schedule_types.get(habit.schedule_type_id), "Неизвестно")
                
                # Проверяем, выполнена ли привычка сегодня
                today_completion = await db.execute(
                    select(HabitCompletion)
                    .where(HabitCompletion.habit_id == habit.id)
                    .where(HabitCompletion.completion_date == date.today())
                    .where(HabitCompletion.is_completed == True)
                )
                is_completed_today = today_completion.scalar_one_or_none() is not None
                today_status = "✅ Выполнено" if is_completed_today else "❌ Не выполнено"
                
                # Вычисляем текущую серию
                current_streak = await calculate_current_streak(db, habit.id)
                streak_text = f"{current_streak} дней" if current_streak > 0 else "нет серии"
                
                message += f"{i}. {status} {habit.name}\n"
                message += f"   📅 {schedule_type_name} | {today_status} | 🔥 {streak_text}\n\n"
                
                # Добавляем кнопку для каждой привычки
                button_text = f"{i}. {habit.name}"
                keyboard.append([InlineKeyboardButton(button_text, callback_data=f"delete_{habit.id}")])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await _send_reply(update, message)
            await update.message.reply_text("Нажмите на привычку, которую хотите удалить:", reply_markup=reply_markup)
            break
            
    except Exception as e:
        logger.error(f"Ошибка при получении привычек для удаления: {e}")
        await _send_reply(update, "Произошла ошибка при получении списка привычек.")


async def handle_delete_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обрабатывает выбор привычки для удаления и запрашивает подтверждение.
    """
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith("delete_"):
        habit_id_str = query.data.replace("delete_", "")
        
        try:
            # Преобразуем строку в UUID
            import uuid
            habit_id = uuid.UUID(habit_id_str)
            
            async for db in get_db_session():
                # Получаем привычку по ID
                habit_result = await db.execute(
                    select(Habit).where(Habit.id == habit_id)
                )
                habit = habit_result.scalar_one_or_none()
                
                if not habit:
                    await query.edit_message_text("❌ Привычка не найдена.")
                    return
                
                # Создаем клавиатуру подтверждения
                from telegram import InlineKeyboardButton, InlineKeyboardMarkup
                confirm_keyboard = [
                    [InlineKeyboardButton("✅ Да, удалить", callback_data=f"confirm_delete_{habit.id}")],
                    [InlineKeyboardButton("❌ Нет, отменить", callback_data="cancel_delete")]
                ]
                reply_markup = InlineKeyboardMarkup(confirm_keyboard)
                
                message = f"⚠️ Вы уверены, что хотите удалить привычку '{habit.name}'?\n\n"
                message += f"📝 Название: {habit.name}\n"
                if habit.description:
                    message += f"📄 Описание: {habit.description}\n"
                message += f"⭐ Очки: {habit.base_points}\n\n"
                message += "Это действие нельзя отменить!"
                
                await query.edit_message_text(message, reply_markup=reply_markup)
                break
                
        except Exception as e:
            logger.error(f"Ошибка при получении привычки для удаления: {e}")
            await query.edit_message_text(f"❌ Произошла ошибка: {str(e)}")


async def handle_delete_confirm_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обрабатывает подтверждение удаления привычки.
    """
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith("confirm_delete_"):
        habit_id_str = query.data.replace("confirm_delete_", "")
        
        try:
            # Преобразуем строку в UUID
            import uuid
            habit_id = uuid.UUID(habit_id_str)
            
            async for db in get_db_session():
                # Получаем привычку по ID
                habit_result = await db.execute(
                    select(Habit).where(Habit.id == habit_id)
                )
                habit = habit_result.scalar_one_or_none()
                
                if not habit:
                    await query.edit_message_text("❌ Привычка не найдена.")
                    return
                
                habit_name = habit.name
                
                # Удаляем привычку
                await db.delete(habit)
                await db.commit()
                
                message = f"🗑️ Привычка '{habit_name}' успешно удалена!\n\n"
                message += "Используйте /habits для просмотра обновленного списка."
                
                await query.edit_message_text(message)
                break
                
        except Exception as e:
            logger.error(f"Ошибка при удалении привычки: {e}")
            await query.edit_message_text(f"❌ Произошла ошибка при удалении привычки: {str(e)}")
    
    elif query.data == "cancel_delete":
        await query.edit_message_text("❌ Удаление отменено.")


async def test_notifications(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Команда для тестирования системы уведомлений (только для разработки).
    Показывает только привычки текущего пользователя.
    """
    user = update.effective_user
    if not user:
        await _send_reply(update, "Не удалось получить информацию о пользователе.")
        return

    try:
        from app.core.database import get_db_session
        from app.bot.services.habit_service import get_users_with_uncompleted_daily_habits
        
        async for db in get_db_session():
            # Получаем только привычки текущего пользователя
            from sqlalchemy import select
            from app.models.database import User, Habit, ScheduleType
            
            # Находим пользователя в базе данных
            user_result = await db.execute(
                select(User).where(User.telegram_id == user.id)
            )
            user_obj = user_result.scalar_one_or_none()
            
            if not user_obj:
                await _send_reply(update, "Пользователь не найден в базе данных.")
                break
            
            # Получаем активные привычки текущего пользователя
            habits_result = await db.execute(
                select(Habit, ScheduleType)
                .join(ScheduleType, Habit.schedule_type_id == ScheduleType.id)
                .where(Habit.user_id == user_obj.id)
                .where(Habit.is_active == True)
            )
            user_habits = habits_result.all()
            
            if not user_habits:
                await _send_reply(update, "У вас нет активных привычек.")
                break
            
            # Получаем незавершенные привычки для текущего пользователя
            users_to_notify = await get_users_with_uncompleted_daily_habits(db)
            current_user_data = None
            
            for user_data in users_to_notify:
                if user_data['user'].telegram_id == user.id:
                    current_user_data = user_data
                    break
            
            if not current_user_data or not current_user_data['uncompleted_habits']:
                await _send_reply(update, "Все ваши привычки уже выполнены сегодня!")
                break
            
            # Формируем сообщение только для текущего пользователя
            uncompleted_habits = current_user_data['uncompleted_habits']
            habit_names = [habit.name for habit in uncompleted_habits]
            
            message = (
                f"🧪 **Тестовое напоминание**\n\n"
                f"Привет, {user_obj.first_name or user_obj.username or 'пользователь'}!\n"
                f"Не забудьте выполнить свои привычки:\n\n"
            )
            
            for i, habit_name in enumerate(habit_names, 1):
                message += f"{i}. {habit_name}\n"
            
            message += f"\nИспользуйте /complete <номер> для отметки выполнения."
            
            await _send_reply(update, message)
            break
            
    except Exception as e:
        logger.error(f"Ошибка при тестировании уведомлений: {e}")
        await _send_reply(update, f"Ошибка при тестировании уведомлений: {str(e)}")
