#!/usr/bin/env python3
"""
Скрипт для запуска Telegram-бота трекера привычек.
Использует правильные пути импорта для корректной работы.
"""

import sys
import os
import logging

# Добавляем корневую директорию проекта в путь Python
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("bot.log", encoding="utf-8")
    ]
)

logger = logging.getLogger(__name__)

def main():
    """Запуск бота."""
    try:
        logger.info("Запуск бота трекера привычек...")
        
        # Импортируем и запускаем основную функцию
        from app.main import main as bot_main
        bot_main()
        
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
