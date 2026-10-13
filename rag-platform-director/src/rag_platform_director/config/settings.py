"""Director serivce config"""
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Director serivce config"""
    # Указываем дефолтные значения только для того, что не изменится
    environment: str = "production"
    service_name: str = "director"
    port: int

    # Ключи и урлы делаем опциональными, так как они зависят от провайдера
    openai_api_key: str | None = None
    ollama_base_url: str | None = None
    temperature: float = 0.0

    model_config = SettingsConfigDict(
        extra="ignore",
        env_file_encoding="utf-8"
    )

settings = Settings()
