# Habit Tracker Bot - Docker Setup Script
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   Habit Tracker Bot - Docker Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Проверяем наличие Docker
try {
    $dockerVersion = docker --version
    Write-Host "Docker найден: $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Docker не установлен или не запущен!" -ForegroundColor Red
    Write-Host "Пожалуйста, установите Docker Desktop для Windows" -ForegroundColor Yellow
    Read-Host "Нажмите Enter для выхода"
    exit 1
}

# Проверяем наличие .env файла
if (-not (Test-Path "..\.env")) {
    Write-Host "WARNING: Файл .env не найден!" -ForegroundColor Yellow
    Write-Host "Создайте файл .env на основе docker.env.example" -ForegroundColor Yellow
    Write-Host "и заполните необходимые переменные окружения." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Пример содержимого .env:" -ForegroundColor Cyan
    Write-Host "TELEGRAM_BOT_TOKEN=your_bot_token_here" -ForegroundColor White
    Write-Host "ADMIN_TELEGRAM_ID=1234567890" -ForegroundColor White
    Write-Host ""
    Read-Host "Нажмите Enter для выхода"
    exit 1
}

# Создаем необходимые директории
if (-not (Test-Path "..\data")) {
    New-Item -ItemType Directory -Path "..\data" | Out-Null
    Write-Host "Создана директория data" -ForegroundColor Green
}

if (-not (Test-Path "..\logs")) {
    New-Item -ItemType Directory -Path "..\logs" | Out-Null
    Write-Host "Создана директория logs" -ForegroundColor Green
}

Write-Host "Создание и запуск контейнера..." -ForegroundColor Cyan
Write-Host ""

# Собираем образ
Write-Host "[1/3] Сборка Docker образа..." -ForegroundColor Yellow
docker-compose build

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Ошибка при сборке образа!" -ForegroundColor Red
    Read-Host "Нажмите Enter для выхода"
    exit 1
}

# Запускаем контейнер
Write-Host "[2/3] Запуск контейнера..." -ForegroundColor Yellow
docker-compose up -d

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Ошибка при запуске контейнера!" -ForegroundColor Red
    Read-Host "Нажмите Enter для выхода"
    exit 1
}

# Показываем статус
Write-Host "[3/3] Проверка статуса..." -ForegroundColor Yellow
docker-compose ps

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "   Контейнер успешно запущен!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Для просмотра логов используйте:" -ForegroundColor Cyan
Write-Host "  docker-compose logs -f" -ForegroundColor White
Write-Host ""
Write-Host "Для остановки контейнера используйте:" -ForegroundColor Cyan
Write-Host "  docker-compose down" -ForegroundColor White
Write-Host ""
Write-Host "Для перезапуска контейнера используйте:" -ForegroundColor Cyan
Write-Host "  docker-compose restart" -ForegroundColor White
Write-Host ""

Read-Host "Нажмите Enter для выхода"
