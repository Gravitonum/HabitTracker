@echo off
echo ========================================
echo   Создание .env файла для Docker
echo ========================================

REM Проверяем наличие .env в корне проекта
if exist "..\.env" (
    echo Копируем .env из корня проекта...
    copy "..\.env" ".env"
    echo .env файл скопирован в директорию docker
) else (
    echo .env файл не найден в корне проекта!
    echo Создаем новый .env файл...
    
    echo # Telegram Bot Configuration > .env
    echo TELEGRAM_BOT_TOKEN=your_bot_token_here >> .env
    echo ADMIN_TELEGRAM_ID=1234567890 >> .env
    echo. >> .env
    echo # Database Configuration >> .env
    echo DATABASE_URL=sqlite+aiosqlite:///./data/habits_tracker.db >> .env
    echo. >> .env
    echo # Logging >> .env
    echo LOG_LEVEL=INFO >> .env
    
    echo Создан шаблон .env файла
    echo Отредактируйте файл docker\.env и укажите ваш токен
)

echo.
echo Содержимое .env файла:
type .env

echo.
echo ========================================
echo   Готово! Теперь запустите run_docker.bat
echo ========================================
pause
