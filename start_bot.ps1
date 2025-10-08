# PowerShell скрипт для запуска бота трекера привычек

Write-Host "Запуск бота трекера привычек..." -ForegroundColor Green
Write-Host ""

# Активация виртуального окружения (если существует)
if (Test-Path "venv\Scripts\Activate.ps1") {
    Write-Host "Активация виртуального окружения..." -ForegroundColor Yellow
    & "venv\Scripts\Activate.ps1"
}

# Запуск бота
Write-Host "Запуск бота..." -ForegroundColor Cyan
python start_bot.py

Write-Host ""
Write-Host "Нажмите любую клавишу для выхода..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
