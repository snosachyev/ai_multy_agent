"""Модуль глобальной конфигурации тестирования и общих фикстур.

Этот модуль автоматически подгружается pytest и предоставляет общие инструменты
для изоляции тестируемого сервиса от реальной инфраструктуры (баз данных, сети, API).
"""

from unittest.mock import AsyncMock, Mock
import pytest

from rag_platform_researcher.application.rag import RAGService
from rag_platform_researcher.infrastructure.rag.rerankers import RRFReranker


# =====================================================================
# 2. ФЕЙКОВЫЕ ОБЪЕКТЫ (Заглушки для изоляции доменной логики)
# =====================================================================

class FakeQueryGenerator:
    """Заглушка (Fake) генератора поисковых запросов.
    
    Имитирует декомпозицию пользовательского вопроса на подзапросы для RAG.
    """

    async def generate(self, question: str) -> list[str]:
        """Генерирует фиксированный список подзапросов.

        Args:
            question: Оригинальный вопрос пользователя.

        Returns:
            list[str]: Список сгенерированных строковых запросов для поиска.
        """
        return [
            question,  # Используем переданный вопрос напрямую
            f"Расширенный контекст: {question}",
        ]


class FakeVectorStore:
    """Заглушка (Fake) векторного хранилища документов.
    
    Имитирует семантический поиск по базе данных без реального подключения к ней.
    """

    async def search(
        self,
        query: str,
        limit: int = 5,
        source_ids: list[str] | None = None,
    ) -> list[dict]:
        return [
            {
                "id": f"doc-{i}",
                "content": f"""Найденный контекст по запросу '{query}' (позиция {i}).
                RAG объединяет поиск и генерацию.""",
                "metadata": {
                    "limit_applied": limit,
                    "source_id": source_ids[0] if source_ids else "default-source",
                },
            }
            for i in range(1, min(limit, 2) + 1)
        ]


# =====================================================================
# 3. ДОМЕННЫЕ ФИКСТУРЫ (Компоненты и сервисы системы)
# =====================================================================

@pytest.fixture(name="mock_llm")
def mock_llm_():
    """Фикстура-заглушка языковой модели (LLM).
    
    Создает объект MagicMock со сэмулированным асинхронным методом ainvoke,
    имитирующим генерацию текста моделью.

    Returns:
        Mock: Сконфигурированный объект-заглушка для LLM.
    """
    llm = Mock()
    llm.ainvoke = AsyncMock(
        return_value=Mock(content="Это тестовый ответ.")
    )
    return llm


@pytest.fixture
def rag_service(mock_llm):
    """Фикстура основного бизнес-сервиса RAGService.
    
    Собирает тестируемый объект, внедряя в него фейковые хранилища 
    и изолированный мок языковой модели.

    Args:
        mock_llm: Инжектируемая фикстура заглушки LLM.

    Returns:
        RAGService: Экземпляр готового к тестированию сервиса.
    """
    return RAGService(
        vector_store=FakeVectorStore(),
        query_generator=FakeQueryGenerator(),
        reranker=RRFReranker(),
        llm=mock_llm,
    )
