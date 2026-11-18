"""Файл dependencies.py для микросервиса Researcher"""
from functools import lru_cache
from fastapi import Depends, Request, FastAPI
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
from rag_platform_researcher.infrastructure.rag.qdrant import QdrantVectorStoreAdapter
from rag_platform_researcher.infrastructure.rag.query_generator import LLMQueryGenerator


@lru_cache(maxsize=1)
def get_vector_store() -> VectorStorePort:
    """Создает и кэширует синглтон векторного хранилища согласно настройкам."""
    if settings.vector_store_type == "qdrant":
        return QdrantVectorStoreAdapter(
            url=settings.qdrant_url,
            collection_name=settings.qdrant_collection,
        )
    return ChromaVectorStore(
        host=settings.chroma_host,
        port=settings.chroma_port,
        collection_name=settings.qdrant_collection,
    )


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
