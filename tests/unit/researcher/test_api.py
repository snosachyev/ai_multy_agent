"""
Unit tests for the Researcher component using dependency injection overrides.

Bypasses real vector database initializations and heavy model loading
by mocking the underlying execution logic.
"""

import pytest
from httpx import ASGITransport, AsyncClient

from rag_platform_researcher.main import app
from rag_platform_researcher.dependencies import get_researcher_service


class MockResearcherService:
    """Мок-сервис, имитирующий логику работы ResearcherService без обращения к ChromaDB."""

    async def execute(self, request) -> dict:
        """Имитирует выполнение задачи Researcher по контракту роутера.

        Принимает pydantic-модель запроса и возвращает структурированный ответ,
        полностью удовлетворяющий схеме валидации ResearchResponse.
        """
        return {
            "workflow_id": request.workflow_id,
            "success": True,
            "result": {
                "question": request.task,
                "answer": "RAG (Retrieval-Augmented Generation) — это подход...",
                "context": "Retrieval-Augmented Generation (RAG) is a technique that "
                "grants LLMs access to external data.",
                "documents": [
                    {
                        "id": "doc_1", 
                        "content": "RAG definition data",
                        "metadata": {"source": "mock_db"}
                    }
                ],
                "generated_queries": ["what is rag", "rag definition"],
            },
        }


@pytest.fixture(name='mocked_client')
async def mocked_client_():
    """Unit-клиент: НЕ запускает lifespan (работает мгновенно без либ и докера)."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as cl:
        yield cl


@pytest.fixture(name="mock_researcher")
def mock_researcher_():
    """Настройка: подменяем зависимость перед тестом"""
    app.dependency_overrides[get_researcher_service] = MockResearcherService
    yield
    # Очистка: сработает ВСЕГДА после завершения теста
    app.dependency_overrides.clear()


@pytest.mark.unit
@pytest.mark.anyio
@pytest.mark.usefixtures("mock_researcher")
async def test_researcher_mocked(mocked_client):
    """Тест контракта эндпоинта /search без запуска lifespan."""
    response = await mocked_client.post(
        "/api/v1/researcher/search",
        json={
            "workflow_id": "ea881a87-7519-46b1-8fdc-6f42ddb1c313",
            "task": "Что такое RAG?",
        },
    )
    assert response.status_code == 200
    assert response.json()["success"] is True
