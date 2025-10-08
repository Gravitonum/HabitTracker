# Инструкции по развертыванию HabitTracker

## 🚀 Быстрый старт

### 1. Получение токена бота

1. Откройте Telegram и найдите [@BotFather](https://t.me/BotFather)
2. Отправьте команду `/newbot`
3. Следуйте инструкциям для создания бота
4. Сохраните полученный токен

### 2. Клонирование и настройка

```bash
# Клонирование репозитория
git clone https://github.com/Gravitonum/HabitTracker.git
cd HabitTracker

# Создание виртуального окружения
python -m venv venv

# Активация окружения
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Установка зависимостей
pip install -r requirements.txt
```

### 3. Настройка конфигурации

```bash
# Копирование примера конфигурации
cp env.example .env

# Редактирование .env файла
# Замените your_bot_token_here на ваш токен
```

### 4. Инициализация базы данных

```bash
python -c "from app.core.database import init_db; import asyncio; asyncio.run(init_db())"
```

### 5. Запуск бота

```bash
python app/main.py
```

## 🐳 Docker развертывание

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "app/main.py"]
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  habit-tracker:
    build: .
    environment:
      - TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
      - DATABASE_URL=sqlite:///./habits_tracker.db
    volumes:
      - ./habits_tracker.db:/app/habits_tracker.db
    restart: unless-stopped
```

### Запуск с Docker

```bash
# Сборка образа
docker build -t habit-tracker .

# Запуск контейнера
docker run -d \
  --name habit-tracker \
  -e TELEGRAM_BOT_TOKEN=your_token_here \
  -v $(pwd)/habits_tracker.db:/app/habits_tracker.db \
  habit-tracker
```

## ☁️ Облачное развертывание

### Heroku

1. Создайте приложение на Heroku
2. Установите Heroku CLI
3. Настройте переменные окружения:

```bash
heroku config:set TELEGRAM_BOT_TOKEN=your_token_here
```

4. Разверните приложение:

```bash
git push heroku main
```

### Railway

1. Подключите GitHub репозиторий
2. Настройте переменные окружения в панели Railway
3. Приложение автоматически развернется

### VPS/Сервер

1. Установите Python 3.12+ и Git
2. Клонируйте репозиторий
3. Настройте systemd service:

```ini
[Unit]
Description=HabitTracker Bot
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/HabitTracker
Environment=PATH=/path/to/HabitTracker/venv/bin
ExecStart=/path/to/HabitTracker/venv/bin/python app/main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

4. Запустите сервис:

```bash
sudo systemctl enable habit-tracker
sudo systemctl start habit-tracker
```

## 🔧 Настройка планировщика

### Время напоминаний

По умолчанию напоминания отправляются в 18:00. Для изменения:

```python
# В app/core/scheduler.py
scheduler.add_job(
    send_daily_reminders,
    "cron",
    hour=9,  # 9:00 утра
    minute=0
)
```

### Часовой пояс

```python
import pytz

# Установка часового пояса
scheduler = AsyncIOScheduler(timezone=pytz.timezone('Europe/Moscow'))
```

## 📊 Мониторинг

### Логирование

```python
import logging

# Настройка логирования в файл
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
```

### Health Check

Добавьте endpoint для проверки состояния:

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/health")
async def health_check():
    return {"status": "ok", "bot": "running"}
```

## 🔒 Безопасность

### Переменные окружения

Никогда не коммитьте файл `.env`:

```gitignore
.env
*.db
__pycache__/
*.pyc
```

### Ограничения доступа

```python
# В app/main.py добавьте проверку пользователей
ALLOWED_USERS = [123456789, 987654321]  # Telegram ID пользователей

async def is_user_allowed(user_id: int) -> bool:
    return user_id in ALLOWED_USERS
```

## 🚨 Устранение неполадок

### Бот не отвечает

1. Проверьте токен бота
2. Убедитесь, что бот запущен
3. Проверьте логи на ошибки

### Ошибки базы данных

1. Проверьте права доступа к файлу БД
2. Убедитесь, что БД инициализирована
3. Проверьте подключение к БД

### Проблемы с планировщиком

1. Проверьте часовой пояс
2. Убедитесь, что планировщик запущен
3. Проверьте настройки cron

## 📈 Масштабирование

### Горизонтальное масштабирование

Для обработки большого количества пользователей:

1. Используйте PostgreSQL вместо SQLite
2. Добавьте Redis для кэширования
3. Используйте несколько экземпляров бота с балансировщиком

### Вертикальное масштабирование

1. Увеличьте ресурсы сервера
2. Оптимизируйте запросы к БД
3. Добавьте индексы в БД

## 🔄 Обновления

### Автоматические обновления

```bash
# Скрипт обновления
#!/bin/bash
git pull origin main
pip install -r requirements.txt
systemctl restart habit-tracker
```

### Резервное копирование

```bash
# Бэкап базы данных
cp habits_tracker.db habits_tracker_backup_$(date +%Y%m%d).db
```
