#!/usr/bin/env python3
"""
Скрипт для отладки переменных окружения в Docker контейнере.
"""

import os
from pathlib import Path

print("=== Docker Environment Debug ===")
print(f"Current working directory: {os.getcwd()}")
print(f"Python path: {os.environ.get('PYTHONPATH', 'Not set')}")

print("\n=== Environment Variables ===")
env_vars = [
    'TELEGRAM_BOT_TOKEN',
    'ADMIN_TELEGRAM_ID', 
    'DATABASE_URL',
    'LOG_LEVEL',
    'PYTHONPATH'
]

for var in env_vars:
    value = os.environ.get(var, 'NOT SET')
    if var == 'TELEGRAM_BOT_TOKEN' and value != 'NOT SET':
        # Скрываем токен для безопасности
        value = f"{value[:10]}...{value[-4:]}" if len(value) > 14 else "***"
    print(f"{var}: {value}")

print("\n=== .env File Search ===")
env_paths = [
    Path(".env"),
    Path("../.env"),
    Path("/app/.env"),
    Path("/app/../.env")
]

for env_path in env_paths:
    exists = env_path.exists()
    print(f"{env_path}: {'EXISTS' if exists else 'NOT FOUND'}")
    if exists:
        print(f"  Absolute path: {env_path.absolute()}")
        try:
            with open(env_path, 'r') as f:
                lines = f.readlines()
                print(f"  Lines: {len(lines)}")
                for line in lines[:3]:  # Показываем первые 3 строки
                    print(f"    {line.strip()}")
        except Exception as e:
            print(f"  Error reading file: {e}")

print("\n=== File System ===")
print("Contents of /app:")
try:
    for item in Path("/app").iterdir():
        print(f"  {item.name} ({'dir' if item.is_dir() else 'file'})")
except Exception as e:
    print(f"Error listing /app: {e}")

print("Contents of current directory:")
try:
    for item in Path(".").iterdir():
        print(f"  {item.name} ({'dir' if item.is_dir() else 'file'})")
except Exception as e:
    print(f"Error listing current directory: {e}")
