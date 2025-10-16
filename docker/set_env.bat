@echo off
echo ========================================
echo   Установка переменных окружения
echo ========================================

echo Введите ваш Telegram Bot Token:
set /p BOT_TOKEN="TELEGRAM_BOT_TOKEN: "

echo Введите ваш Telegram ID (для админа):
set /p ADMIN_ID="ADMIN_TELEGRAM_ID: "

echo.
echo Устанавливаем переменные окружения...

REM Устанавливаем переменные для текущей сессии
set TELEGRAM_BOT_TOKEN=%BOT_TOKEN%
set ADMIN_TELEGRAM_ID=%ADMIN_ID%

echo.
echo Переменные установлены:
echo TELEGRAM_BOT_TOKEN=%BOT_TOKEN%
echo ADMIN_TELEGRAM_ID=%ADMIN_ID%

echo.
echo Запускаем Docker Compose...
docker-compose up --build -d

echo.
echo ========================================
echo   Готово! Проверьте логи:
echo   docker-compose logs -f
echo ========================================
pause
