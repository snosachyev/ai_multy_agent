"""Файл dependencies.py"""
from fastapi import Depends
from langchain_core.language_models import BaseChatModel
# Импортируем общую фабрику и конфиг микросервиса
from rag_platform_llm import LLMConfig, create_llm
from rag_platform_analyst.config.settings import settings
from rag_platform_analyst.application.analyst import AnalystService


def get_llm() -> BaseChatModel:
    """Зависимость для создания инстанса LLM."""
    return create_llm(
        LLMConfig(
            provider=settings.provider,
            model=settings.llm_model,
            temperature=0,
            base_url=settings.ollama_base_url,
            api_key=settings.openai_api_key,
        )
    )

def get_analyst_service(llm: BaseChatModel = Depends(get_llm)) -> AnalystService:
    """Зависимость для создания сервиса аналитики."""
    return AnalystService(llm=llm)
