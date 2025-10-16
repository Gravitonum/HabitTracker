# Используем официальный Python образ
FROM python:3.12-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Копируем файл зависимостей
COPY requirements.txt .

# Устанавливаем Python зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем .env файл если он существует (до копирования всего кода)
COPY .env* ./

# Копируем код приложения
COPY . .

# Создаем директорию для базы данных
RUN mkdir -p /app/data

# Устанавливаем переменные окружения по умолчанию
ENV PYTHONPATH=/app
ENV DATABASE_URL=sqlite+aiosqlite:///./data/habits_tracker.db
ENV LOG_LEVEL=INFO

# Создаем пользователя для безопасности
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app
USER app

# Скрипт инициализации базы данных
COPY docker/init_db.py ./

# Команда по умолчанию
CMD ["sh", "-c", "python docker/init_db.py && python app/main.py"]

# Отладочная команда (раскомментируйте для отладки)
# CMD ["python", "docker/debug_env.py"]
