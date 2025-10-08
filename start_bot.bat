@echo off
echo Запуск бота трекера привычек...
echo.

REM Активация виртуального окружения (если существует)
if exist "venv\Scripts\activate.bat" (
    echo Активация виртуального окружения...
    call venv\Scripts\activate.bat
)

REM Запуск бота
python start_bot.py

pause
