"""Модуль http запросов"""

import httpx


class ServiceClient:
    """Класс ServiceClient для работы с http запросами"""
    def __init__(
        self,
        client: httpx.AsyncClient,  # Передаем общий сессионный клиент приложения
        base_url: str,
    ):
        self.base_url = base_url.rstrip("/")
        self.client = client  # Ссылка на общий пул соединений

    # Метод close() здесь НЕ НУЖЕН, так как за закрытие отвечает lifespan
