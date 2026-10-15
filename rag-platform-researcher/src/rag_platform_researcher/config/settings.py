"""Researcher serivce config"""
import os
from pathlib import Path
from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

# settings.py лежит в config/, значит .parent.parent — это корень пакета
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent


class Settings(BaseSettings):
    """Researcher service config"""
    environment: str = "production"
    service_name: str = "researcher"
    port: int

    # Если значений нет в окружении, Pydantic потребует их указать
    provider: str  # "ollama" или "openai"
    llm_model: str  # "qwen2.5:7b" или "gpt-4o-mini"

    # Ключи и урлы делаем опциональными, так как они зависят от провайдера
    openai_api_key: str | None = None
    ollama_base_url: str | None = None
    temperature: float = 0.0

    # вывод логов
    debug_rag: bool = False

    splits_file_name: str = "chunked.pkl"

    # В Docker сюда прилетит "/data" из docker-compose.yaml. 
    # Локально на ПК значение по умолчанию будет "data" (относительный путь).
    data_dir: str = "/data"

    @computed_field
    def splits_path(self) -> Path:
        """Возвращает чистый абсолютный путь к файлу сплитов."""
        full_path = os.path.join(self.data_dir, self.splits_file_name)
        return Path(full_path)

    model_config = SettingsConfigDict(
        extra="ignore",
        env_file_encoding="utf-8"
    )

settings = Settings()
