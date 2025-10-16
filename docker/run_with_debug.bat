@echo off
echo ========================================
echo   Habit Tracker Bot - Debug Mode
echo ========================================

REM Останавливаем и удаляем старый контейнер
echo Остановка старого контейнера...
docker-compose down 2>nul

REM Пересобираем образ
echo Пересборка образа...
docker-compose build --no-cache

REM Запускаем контейнер в режиме отладки
echo Запуск в режиме отладки...
docker-compose run --rm habit-tracker-bot python docker/debug_env.py

echo.
echo ========================================
echo   Отладка завершена
echo ========================================
pause
