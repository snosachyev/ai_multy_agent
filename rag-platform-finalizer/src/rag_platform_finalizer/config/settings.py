"""Finalizer serivce config"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Finalizer service config"""
    environment: str = "production"
    service_name: str = "finalizer"
    port: int

    # Если значений нет в окружении, Pydantic потребует их указать
    provider: str  # "ollama" или "openai"
    llm_model: str  # "qwen2.5:7b" или "gpt-4o-mini"

    # Ключи и урлы делаем опциональными, так как они зависят от провайдера
    openai_api_key: str | None = None
    ollama_base_url: str | None = None
    temperature: float = 0.0

    model_config = SettingsConfigDict(
        extra="ignore",
        env_file_encoding="utf-8"
    )

settings = Settings()
