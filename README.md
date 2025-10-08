# HabitTracker - Telegram Bot для отслеживания привычек

## 📋 Описание проекта

HabitTracker - это Telegram-бот для отслеживания и управления привычками с элементами геймификации. Бот помогает пользователям формировать полезные привычки, отслеживать прогресс и мотивирует через систему очков, серий и достижений.

### ✨ Основные возможности

- **Создание привычек** с различными типами расписания:
  - Ежедневные привычки
  - Еженедельные привычки  
  - Настраиваемые расписания (custom)
- **Интерактивное управление** через кнопки и диалоги
- **Система геймификации**:
  - Очки за выполнение привычек
  - Серии (streaks) выполнения
  - Уровни и достижения
  - Таблица лидеров
- **Уведомления и напоминания** о незавершенных привычках
- **Подробная статистика** по всем привычкам
- **Управление привычками** (создание, удаление, отметка выполнения)

### 🎯 Типы расписания

1. **Ежедневно** - напоминания каждый день в 18:00
2. **Еженедельно** - напоминания раз в неделю
3. **Свой график (Custom)** - настраиваемое расписание:
   - Выбор дней недели (пн,вт,ср,чт,пт,сб,вс)
   - Настройка времени напоминания (HH:MM)
   - Установка частоты выполнения (каждый N день)

## 🚀 Установка и запуск

### Предварительные требования

- Python 3.12
- Git
- Telegram Bot Token (получить у [@BotFather](https://t.me/BotFather))

### 1. Клонирование репозитория

```bash
git clone https://github.com/Gravitonum/HabitTracker.git
cd HabitTracker
```

### 2. Создание виртуального окружения

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/macOS
python3 -m venv venv
source venv/bin/activate
```

### 3. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 4. Настройка переменных окружения

Создайте файл `.env` в корне проекта:

```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
```

### 5. Инициализация базы данных

```bash
python -c "from app.core.database import init_db; import asyncio; asyncio.run(init_db())"
```

### 6. Запуск бота

```bash
# Способ 1: Прямой запуск
python app/main.py

# Способ 2: Через скрипт
python start_bot.py

# Способ 3: Через PowerShell (Windows)
.\start_bot.ps1

# Способ 4: Через Batch (Windows)
start_bot.bat
```

## 📱 Использование

### Основные команды

- `/start` - Начать работу с ботом
- `/help` - Показать справку по командам
- `/habits` - Посмотреть список ваших привычек
- `/create_habit` - Создать новую привычку (интерактивно)
- `/complete` - Отметить привычку как выполненную
- `/delete_habit` - Удалить привычку
- `/stats` - Посмотреть подробную статистику
- `/profile` - Посмотреть свой профиль (уровень, очки, серии)
- `/rewards` - Посмотреть награды и достижения
- `/leaderboard` - Таблица лидеров

### Создание привычки

1. Отправьте `/create_habit`
2. Выберите тип расписания (Ежедневно/Еженедельно/Свой график)
3. Введите название привычки
4. Введите описание (необязательно, можно пропустить командой `/skip`)
5. Готово! Привычка создана

### Отметка выполнения

1. Отправьте `/complete`
2. Выберите привычку из списка кнопок
3. Привычка отмечена как выполненная

### Удаление привычки

1. Отправьте `/delete_habit`
2. Выберите привычку из списка
3. Подтвердите удаление
4. Привычка удалена навсегда

## 🏗️ Разработка

### Структура проекта

```
HabitTracker/
├── app/
│   ├── bot/                    # Telegram Bot логика
│   │   ├── handlers/           # Обработчики команд
│   │   └── services/           # Бизнес-логика
│   ├── core/                   # Основные компоненты
│   ├── models/                 # Модели данных
│   └── utils/                  # Утилиты
├── habits_tracker.db           # SQLite база данных
└── requirements.txt            # Зависимости
```

### Основные технологии

- **Python 3.12+** - Основной язык
- **python-telegram-bot** - Telegram Bot API
- **SQLAlchemy** - ORM для работы с БД
- **FastAPI** - Веб-фреймворк (для API)
- **Pydantic** - Валидация данных
- **APScheduler** - Планировщик задач
- **SQLite** - База данных

### Добавление новых команд

1. Создайте обработчик в `app/bot/handlers/`
2. Добавьте команду в `app/main.py`
3. Обновите справку в функции `help_command`
4. Добавьте команду в `setup_bot_commands`

### Работа с базой данных

```python
from app.core.database import get_db_session
from app.models.database import User, Habit

async def example_function():
    async for db in get_db_session():
        # Ваш код работы с БД
        result = await db.execute(select(User))
        users = result.scalars().all()
```

## 🔧 Конфигурация

### Переменные окружения

- `TELEGRAM_BOT_TOKEN` - Токен бота от BotFather


### Настройка планировщика

Время отправки напоминаний настраивается в `app/core/scheduler.py`:

```python
# Ежедневные напоминания в 18:00
scheduler.add_job(
    send_daily_reminders,
    "cron",
    hour=18,
    minute=0
)
```

## 🐛 Отладка

### Логи

Логи сохраняются в консоль. Для детальной отладки:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Тестирование команд

Используйте команду `/test_notifications` для проверки системы уведомлений.

### Проверка базы данных

```bash
python -c "from app.core.database import check_db; import asyncio; asyncio.run(check_db())"
```

## 🤝 Вклад в проект

### Процесс разработки

1. **Создайте форк** репозитория
2. **Создайте ветку** для новой функции: `git checkout -b feature/amazing-feature`
3. **Внесите изменения** и зафиксируйте их: `git commit -m 'Add amazing feature'`
4. **Отправьте в ветку**: `git push origin feature/amazing-feature`
5. **Создайте Pull Request** в основной репозиторий

### Правила

- Ветка `main` защищена - все изменения только через Pull Request
- Код должен быть покрыт тестами
- Следуйте стилю кода проекта (PEP 8)
- Обновляйте документацию при необходимости

## 📄 Лицензия

Этот проект распространяется под лицензией MIT. См. файл `LICENSE` для подробностей.

## 📞 Поддержка

Если у вас возникли вопросы или проблемы:

1. Проверьте [Issues](https://github.com/Gravitonum/HabitTracker/issues)
2. Создайте новый Issue с подробным описанием
3. Обратитесь к разработчикам

## 🎉 Благодарности

- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) - Отличная библиотека для Telegram Bot API
- [SQLAlchemy](https://www.sqlalchemy.org/) - Мощный ORM для Python
- [FastAPI](https://fastapi.tiangolo.com/) - Современный веб-фреймворк

---

**Сделано с ❤️ для формирования полезных привычек**
