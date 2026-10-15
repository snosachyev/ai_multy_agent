"""Файл dependencies.py для микросервиса Researcher"""
from typing import Optional
from fastapi import Depends
from langchain_core.language_models import BaseChatModel

# 1. Ваши общие фабрики
from rag_platform_llm import LLMConfig, create_llm
from rag_platform_researcher.config.settings import settings

# 2. Бизнес-логика (Порты)
from rag_platform_researcher.application.rag import (
    RAGService,
    VectorStorePort,
    QueryGeneratorPort,
)
from rag_platform_researcher.application.researcher import ResearcherService

# 3. Реальные классы (Адаптеры), которые вы скинули
from rag_platform_researcher.infrastructure.rag.chroma import ChromaVectorStore
from rag_platform_researcher.infrastructure.rag.query_generator import LLMQueryGenerator

# Глобальная переменная для хранения единственного экземпляра базы в памяти
_vector_store_instance: Optional[ChromaVectorStore] = None


def init_vector_store() -> None:
    """Инициализирует векторное хранилище один раз при старте приложения."""
    global _vector_store_instance
    if _vector_store_instance is not None:
        return

    # Проверяем физическое наличие файла на диске перед тем как читать его
    if not settings.splits_path.exists():
        raise FileNotFoundError(
            f"❌ КРИТИЧЕСКАЯ ОШИБКА: Файл векторных сплитов не найден по пути: "
            f"{settings.splits_path.absolute()}. "
            f"Проверьте монтирование volumes в Docker или наличие файла локально."
        )

    _vector_store_instance = ChromaVectorStore(splits_path=str(settings.splits_path))


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


def get_vector_store() -> VectorStorePort:
    """Зависимость для получения уже инициализированного векторного хранилища.
    
    Отрабатывает мгновенно, не пересоздавая базу в памяти на каждый запрос.
    """
    if _vector_store_instance is None:
        raise RuntimeError("Vector store is not initialized. Call init_vector_store() on startup.")
    return _vector_store_instance


def get_query_generator(llm: BaseChatModel = Depends(get_llm)) -> QueryGeneratorPort:
    """Зависимость для генератора альтернативных поисковых запросов."""
    # Используем ваш класс LLMQueryGenerator
    return LLMQueryGenerator(llm=llm)


def get_rag_service(
    vector_store: VectorStorePort = Depends(get_vector_store),
    query_generator: QueryGeneratorPort = Depends(get_query_generator),
    llm: BaseChatModel = Depends(get_llm),
) -> RAGService:
    """Зависимость для сборки ядра RAG-логики."""
    return RAGService(
        vector_store=vector_store,
        query_generator=query_generator,
        llm=llm,
    )


def get_researcher_service(
    rag_service: RAGService = Depends(get_rag_service),
) -> ResearcherService:
    """Создает фасад ResearcherService для использования в роутерах."""
    return ResearcherService(rag_service=rag_service)
