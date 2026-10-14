"""Поисковик хранилища"""
import time

from abc import ABC, abstractmethod
from typing import Any, Dict, List

from rag_platform_contracts.researcher import (
    RAGResult
)

from rag_platform_researcher.application.metrics import (
    SERVICE_NAME,
    RAG_REQUESTS_TOTAL,
    RAG_REQUEST_ERRORS_TOTAL,
    RAG_REQUEST_DURATION,
    RAG_QUERY_GENERATION_DURATION,
    RAG_GENERATED_QUERIES,
    RAG_RETRIEVAL_DURATION,
    RAG_RETRIEVED_DOCUMENTS,
    RAG_CONTEXT_DOCUMENTS,
    RAG_LLM_DURATION,
)
from rag_platform_researcher.config.settings import settings

from rag_platform_observability.observability import get_logger


logger = get_logger(__name__)


class VectorStorePort(ABC):
    """Порт для взаимодействия с векторным хранилищем документов."""

    @abstractmethod
    async def search(
        self,
        query: str,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """Выполняет семантический поиск релевантных документов по векторизованному запросу.

        Args:
            query: Текстовый поисковый запрос.
            limit: Максимальное количество возвращаемых документов. Defaults to 5.

        Returns:
            List[Dict[str, Any]]: Список словарей, содержащих метаданные и контент документов.
        """


class QueryGeneratorPort(ABC):
    """Порт для расширения и генерации поисковых запросов."""

    @abstractmethod
    async def generate(
        self,
        question: str,
    ) -> List[str]:
        """Генерирует альтернативные варианты поисковых запросов на основе исходного вопроса.

        Args:
            question: Исходный вопрос пользователя.

        Returns:
            List[str]: Список сгенерированных поисковых формулировок.
        """


class RAGService:
    """Ядро бизнес-логики RAG (Retrieval-Augmented Generation).

    Обеспечивает координацию процессов генерации запросов, поиска в векторной базе,
    дедупликации результатов, а также осуществляет сбор Prometheus-метрик.
    """
    def __init__(
        self,
        vector_store: VectorStorePort,
        query_generator: QueryGeneratorPort,
        llm,
    ) -> None:
        """Инициализирует RAG-сервис необходимыми компонентами и интерфейсами.

        Args:
            vector_store: Реализация порта для работы с векторным хранилищем.
            query_generator: Реализация порта для расширения поисковых запросов.
            llm: Объект языковой модели для генерации ответов или анализа.
        """
        self.vector_store = vector_store
        self.query_generator = query_generator
        self.llm = llm

    async def execute(
        self,
        task: str,
    ) -> RAGResult:
        """Инициализирует RAG-сервис необходимыми компонентами и интерфейсами.

        Args:
            vector_store: Реализация порта для работы с векторным хранилищем.
            query_generator: Реализация порта для расширения поисковых запросов.
            llm: Объект языковой модели для генерации ответов или анализа.
        """
        request_start = time.perf_counter()

        RAG_REQUESTS_TOTAL.labels(
            service=SERVICE_NAME
        ).inc()

        # --------------------------------------------------
        # 1. Generate multiple search queries
        # --------------------------------------------------
        try:
            query_generation_start = time.perf_counter()

            queries = await self.query_generator.generate(task)

            query_generation_duration = (
                time.perf_counter() - query_generation_start
            )

            RAG_QUERY_GENERATION_DURATION.labels(
                service=SERVICE_NAME
            ).observe(query_generation_duration)

            if not queries:
                queries = [task]

            RAG_GENERATED_QUERIES.labels(
                service=SERVICE_NAME
            ).observe(len(queries))


            if settings.debug_rag:
                logger.debug(f"\n {"=" * 80}\n ORIGINAL QUESTION \n{"=" * 80}\n {task}")

                logger.debug(f"\n {"=" * 80}\n GENERATED QUERIES \n{"=" * 80}\n {task}")

                for index, query in enumerate(queries, start=1):
                    logger.debug(f"\n {index}. {query}")

            # --------------------------------------------------
            # 2. Search for every query
            # --------------------------------------------------

            # ============================================================
            # 2. RETRIEVAL
            # ============================================================

            retrieval_start = time.perf_counter()

            # content -> document info
            documents_by_id: dict[str, dict] = {}

            for query_index, query in enumerate(queries):
                if settings.debug_rag:
                    logger.debug(
                        f"\n {"=" * 80}\n RETRIEVAL FOR QUERY {query_index}\n{"=" * 80}\n {query}"
                    )

                retrieved_documents = await self.vector_store.search(
                    query=query,
                    limit=5,
                )

                RAG_RETRIEVED_DOCUMENTS.labels(
                    service=SERVICE_NAME
                ).observe(len(retrieved_documents))

                if settings.debug_rag:
                    logger.debug(f"\n Retrieved documents: {len(retrieved_documents)}")

                for document_index, document in enumerate(
                    retrieved_documents,
                    start=1,
                ):
                    content = document["content"]

                    if settings.debug_rag:
                        logger.debug(f"\n {"-" * 80}\n QUERY {query_index} \
                                      /\nDOCUMENT {document_index}\n{"-" * 80}\n{content[:1000]}")
                    # ------------------------------------------
                    # Deduplicate by content
                    # ------------------------------------------

                    document_id = document["id"]

                    if document_id not in documents_by_id:
                        documents_by_id[document_id] = {
                            **document,
                            "matched_queries": [query_index],
                        }
                    else:
                        documents_by_id[document_id]["matched_queries"].append(
                            query_index
                        )

            retrieval_duration = (
                time.perf_counter() - retrieval_start
            )

            RAG_RETRIEVAL_DURATION.labels(
                service=SERVICE_NAME
            ).observe(retrieval_duration)


            # ============================================================
            # 3. RANK DOCUMENTS
            # ============================================================

            documents = list(documents_by_id.values())

            if not documents:
                return "В документах ничего не найдено."

            # --------------------------------------------------
            # 3. Sort documents by number of matching queries
            # --------------------------------------------------
            #
            # Если один и тот же chunk найден несколькими
            # generated queries, это дополнительный сигнал
            # его релевантности.
            #

            documents.sort(
                key=lambda document: len(
                    set(document["matched_queries"])
                ),
                reverse=True,
            )

            # --------------------------------------------------
            # 4. Debug final documents
            # --------------------------------------------------

            if settings.debug_rag:
                logger.debug(f"\n {"=" * 80}\n FINAL UNIQUE DOCUMENTS\n {"=" * 80}")

            RAG_CONTEXT_DOCUMENTS.labels(
                service=SERVICE_NAME
            ).observe(len(documents))


            # ============================================================
            # 4. BUILD CONTEXT
            # ============================================================

            for index, document in enumerate(documents, start=1):
                matched_queries = sorted(
                    set(document["matched_queries"])
                )

                if settings.debug_rag:
                    logger.debug(f"\n {"-" * 80}\nDOCUMENT{index} \
                                  | \nMATCHED QUERIES: {matched_queries}\n{"-" * 80}\n \
                                  {document["content"][:1500]}")

            # --------------------------------------------------
            # 5. Build context
            # --------------------------------------------------

            context_parts = []

            for index, document in enumerate(documents, start=1):

                context_parts.append(
                    f"""
                    [DOCUMENT {index}]

                    {document["content"]}
                    """
                )

            context = "\n\n".join(context_parts)

            # --------------------------------------------------
            # 6. RAG prompt
            # --------------------------------------------------

            # ============================================================
            # 5. FINAL LLM
            # ============================================================

            prompt = f"""
            Ты — исследователь, работающий с базой документов.

            Ответь на вопрос пользователя, используя только информацию
            из переданного контекста.

            ВАЖНО:
            - Вопрос пользователя написан на русском языке.
            - Ответ ОБЯЗАТЕЛЬНО должен быть на русском языке.
            - Английский текст из контекста переводи на русский.
            - Не копируй язык контекста как язык ответа.

            Правила:

            1. Используй только информацию из контекста.
            2. Если контекст содержит информацию, позволяющую
            однозначно ответить на вопрос, дай ответ прямо.
            3. Если точное определение отсутствует как отдельная фраза,
            но оно однозначно следует из нескольких фрагментов,
            синтезируй их в одно определение.
            4. Если в контексте есть примеры или способы реализации,
            сначала дай определение, затем примеры.
            5. Не добавляй внешние знания.
            6. Не выдумывай факты.
            7. Если информации действительно недостаточно,
            скажи об этом прямо.
            8. Не упоминай RAG, retrieval, generated queries,
            vector store или внутреннюю работу системы.

            Контекст:

            {context}

            Вопрос пользователя:

            {task}

            Ответ:
            """

            if settings.debug_rag:
                logger.debug(f"\n {"=" * 80}\nFINAL CONTEXT\n{"=" * 80}\n{context}")

            # --------------------------------------------------
            # 7. Generate answer
            # --------------------------------------------------

            llm_start = time.perf_counter()

            response = await self.llm.ainvoke(prompt)

            llm_duration = time.perf_counter() - llm_start

            RAG_LLM_DURATION.labels(
                service=SERVICE_NAME
            ).observe(llm_duration)

            # ============================================================
            # 6. RETURN
            # ============================================================

            return RAGResult(
                question=task,
                generated_queries=queries,
                documents=documents,
                context=context,
                answer=response.content,
            )


        except Exception:
            RAG_REQUEST_ERRORS_TOTAL.labels(
                service=SERVICE_NAME
            ).inc()

            raise


        finally:

            request_duration = (
                time.perf_counter() - request_start
            )

            RAG_REQUEST_DURATION.labels(
                service=SERVICE_NAME
            ).observe(request_duration)
