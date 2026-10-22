"""Модуль конфигурации"""
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)


class Settings(BaseSettings):
    """Класс конфигурации"""
    environment: str = "production"

    port: int = 8000

    director_service_url: str = (
        "http://director:8001"
    )

    researcher_service_url: str = (
        "http://researcher:8002"
    )

    analyst_service_url: str = (
        "http://analyst:8003"
    )

    finalizer_service_url: str = (
        "http://finalizer:8004"
    )

    max_iterations: int = 6

    # вывод логов
    debug_rag: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()
