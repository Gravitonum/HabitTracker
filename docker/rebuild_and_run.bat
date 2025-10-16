@echo off
echo ========================================
echo   Пересборка и запуск с инициализацией БД
echo ========================================

REM Останавливаем и удаляем старый контейнер
echo Остановка старого контейнера...
docker-compose down

REM Удаляем старый образ
echo Удаление старого образа...
docker rmi habit-tracker-bot 2>nul

REM Создаем директории
if not exist "..\data" mkdir "..\data"
if not exist "..\logs" mkdir "..\logs"

REM Пересобираем образ
echo Пересборка образа...
docker-compose build --no-cache

REM Запускаем контейнер
echo Запуск контейнера...
docker-compose up -d

echo.
echo ========================================
echo   Контейнер запущен!
echo ========================================
echo.
echo Проверяем логи...
timeout /t 3 /nobreak >nul
docker-compose logs --tail=20

echo.
echo Для просмотра всех логов используйте:
echo   docker-compose logs -f
echo.
pause
