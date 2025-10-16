# Docker Setup для Habit Tracker Bot

Этот каталог содержит файлы для запуска Habit Tracker Bot в Docker контейнере.

## Файлы

- `Dockerfile` - Конфигурация Docker образа
- `docker-compose.yml` - Конфигурация для Docker Compose
- `init_db.py` - Скрипт инициализации базы данных
- `run_docker.bat` - Windows batch скрипт для запуска
- `run_docker.ps1` - PowerShell скрипт для запуска
- `docker.env.example` - Пример файла переменных окружения

## Быстрый старт

### 1. Подготовка

1. Убедитесь, что Docker Desktop установлен и запущен
2. Скопируйте `docker.env.example` в `.env` в корне проекта:
   ```bash
   copy docker.env.example ..\.env
   ```
3. Отредактируйте `.env` файл и укажите ваш Telegram Bot Token:
   ```
   TELEGRAM_BOT_TOKEN=your_bot_token_here
   ADMIN_TELEGRAM_ID=your_telegram_id
   ```

### 2. Запуск

#### Windows (Batch)
```cmd
cd docker
run_docker.bat
```

#### Windows (PowerShell)
```powershell
cd docker
.\run_docker.ps1
```

#### Ручной запуск
```bash
cd docker
docker-compose up --build
```

### 3. Управление контейнером

```bash
# Просмотр логов
docker-compose logs -f

# Остановка
docker-compose down

# Перезапуск
docker-compose restart

# Пересборка и запуск
docker-compose up --build
```

## Структура проекта в контейнере

```
/app/
├── app/                 # Код приложения
├── data/               # База данных SQLite
├── logs/               # Логи приложения
├── requirements.txt    # Python зависимости
└── main.py            # Точка входа
```

## Переменные окружения

| Переменная | Описание | По умолчанию |
|------------|----------|--------------|
| `TELEGRAM_BOT_TOKEN` | Токен Telegram бота | - |
| `ADMIN_TELEGRAM_ID` | ID администратора | 1234567890 |
| `DATABASE_URL` | URL базы данных | sqlite+aiosqlite:///./data/habits_tracker.db |
| `LOG_LEVEL` | Уровень логирования | INFO |
| `POINTS_PER_HABIT_COMPLETION` | Очки за выполнение привычки | 10 |
| `STREAK_BONUS_MULTIPLIER` | Множитель бонуса за серию | 0.1 |
| `MAX_STREAK_DAYS` | Максимальная длина серии | 365 |

## Устранение неполадок

### Контейнер не запускается
1. Проверьте, что Docker Desktop запущен
2. Убедитесь, что файл `.env` существует и содержит корректный токен
3. Проверьте логи: `docker-compose logs`

### Ошибки базы данных
1. Убедитесь, что директория `data` создана
2. Проверьте права доступа к директории
3. Попробуйте удалить контейнер и пересоздать: `docker-compose down && docker-compose up --build`

### Проблемы с сетью
1. Проверьте, что порты не заняты другими приложениями
2. Убедитесь, что брандмауэр не блокирует Docker

## Разработка

Для разработки с hot-reload:

```bash
# Монтируем код как volume
docker-compose -f docker-compose.dev.yml up
```

## Продакшн

Для продакшн развертывания:

1. Используйте внешнюю базу данных (PostgreSQL)
2. Настройте логирование в файлы
3. Используйте секреты для токенов
4. Настройте мониторинг и алерты
