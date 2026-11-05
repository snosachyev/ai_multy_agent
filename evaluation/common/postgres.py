"""Модуль для работы с базой данных PostgreSQL в рамках контура эвалюации.

Обеспечивает централизованное создание и конфигурирование подключений
к базе данных результатов тестирования и метрик на основе переменных
окружения.
"""

from __future__ import annotations

import os

import psycopg


def get_connection() -> psycopg.Connection:
    """Создает и возвращает новое синхронное подключение к PostgreSQL.

    Конфигурация параметров подключения (хост, порт, имя БД, учетные данные)
    динамически считывается из переменных окружения. Если переменные не заданы,
    используются дефолтные значения для локального тестового контура Docker.

    Returns:
        psycopg.Connection: Объект активного соединения с базой данных.

    Raises:
        psycopg.OperationalError: Если не удалось установить соединение
            с указанными параметрами.
    """
    return psycopg.connect(
        host=os.getenv(
            "POSTGRES_HOST",
            "postgres",
        ),
        port=int(
            os.getenv(
                "POSTGRES_PORT",
                "5432",
            )
        ),
        dbname=os.getenv(
            "POSTGRES_DB",
            "rag_evaluation",
        ),
        user=os.getenv(
            "POSTGRES_USER",
            "rag",
        ),
        password=os.getenv(
            "POSTGRES_PASSWORD",
            "rag",
        ),
    )
