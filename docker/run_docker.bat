@echo off
echo ========================================
echo   Habit Tracker Bot - Docker Setup
echo ========================================

REM Проверяем наличие Docker
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Docker не установлен или не запущен!
    echo Пожалуйста, установите Docker Desktop для Windows
    pause
    exit /b 1
)

REM Проверяем наличие .env файла
if not exist "..\.env" (
    echo WARNING: Файл .env не найден!
    echo Создайте файл .env на основе docker.env.example
    echo и заполните необходимые переменные окружения.
    echo.
    echo Пример содержимого .env:
    echo TELEGRAM_BOT_TOKEN=your_bot_token_here
    echo ADMIN_TELEGRAM_ID=1234567890
    echo.
    pause
    exit /b 1
)

REM Создаем необходимые директории
if not exist "..\data" mkdir "..\data"
if not exist "..\logs" mkdir "..\logs"

echo Создание и запуск контейнера...
echo.

REM Собираем образ
echo [1/3] Сборка Docker образа...
docker-compose build

if %errorlevel% neq 0 (
    echo ERROR: Ошибка при сборке образа!
    pause
    exit /b 1
)

REM Запускаем контейнер
echo [2/3] Запуск контейнера...
docker-compose up -d

if %errorlevel% neq 0 (
    echo ERROR: Ошибка при запуске контейнера!
    pause
    exit /b 1
)

REM Показываем статус
echo [3/3] Проверка статуса...
docker-compose ps

echo.
echo ========================================
echo   Контейнер успешно запущен!
echo ========================================
echo.
echo Для просмотра логов используйте:
echo   docker-compose logs -f
echo.
echo Для остановки контейнера используйте:
echo   docker-compose down
echo.
echo Для перезапуска контейнера используйте:
echo   docker-compose restart
echo.

pause
