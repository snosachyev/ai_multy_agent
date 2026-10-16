"""Файл dependencies.py для микросервиса Researcher"""
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
from rag_platform_researcher.infrastructure.rag.query_generator import LLMQueryGenerator


def init_vector_store(app: FastAPI) -> None:
    """Инициализирует векторное хранилище один раз при старте приложения и сохраняет в state.
    Вызывается внутри lifespan в main.py.
    """
    # Проверяем физическое наличие файла на диске перед тем как читать его
    if not settings.splits_path.exists():
        raise FileNotFoundError(
            f"❌ КРИТИЧЕСКАЯ ОШИБКА: Файл векторных сплитов не найден по пути: "
            f"{settings.splits_path.absolute()}. "
            f"Проверьте монтирование volumes в Docker или наличие файла локально."
        )

    # Сохраняем экземпляр базы напрямую в стейт переданного FastAPI-приложения
    app.state.vector_store = ChromaVectorStore(splits_path=str(settings.splits_path))


def get_vector_store(request: Request) -> VectorStorePort:
    """Достает созданную базу напрямую из стейта запущенного FastAPI приложения.
    
    Отрабатывает мгновенно, возвращая уже готовую ссылку из памяти.
    """
    # Гарантирует продакшен-изоляцию: объект живет ровно столько, сколько живет инстанс приложения
    return request.app.state.vector_store


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
