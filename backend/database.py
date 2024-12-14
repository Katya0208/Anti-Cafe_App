# backend/database.py

import asyncpg
import os
import logging
from dotenv import load_dotenv
from fastapi import FastAPI

# Загрузка переменных окружения из .env файла
load_dotenv()

# Конфигурация подключения к базе данных
DATABASE_CONFIG = {
    'user': os.getenv('POSTGRES_USER', 'katushka'),
    'password': os.getenv('POSTGRES_PASSWORD', 'rfneirf2004'),  # Важно: Измените пароль для безопасности!
    'database': os.getenv('POSTGRES_DB', 'anticafe'),
    'host': os.getenv('POSTGRES_HOST', '127.0.0.1'),
    'port': int(os.getenv('POSTGRES_PORT', 5432))
}

async def init_db(app: FastAPI):
    """Инициализация пула соединений с базой данных и сохранение его в состоянии приложения."""
    try:
        logging.info(f"Database config: {DATABASE_CONFIG}")
        app.state.pool = await asyncpg.create_pool(**DATABASE_CONFIG)
        logging.info("Pool created")
    except Exception as e:
        logging.error(f"Error connecting to the database: {e}")

async def close_db(app: FastAPI):
    """Закрытие пула соединений с базой данных."""
    if hasattr(app.state, 'pool') and app.state.pool:
        await app.state.pool.close()
        logging.info("Pool closed")