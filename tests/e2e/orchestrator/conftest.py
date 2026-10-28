"""
Fixtures and utilities for orchestrator integration testing.

Provides initialized ASGI application clients, mock request payloads,
and helper factories to simulate workflow runs with full lifespan support.
"""

import pytest
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient

from rag_platform_orchestrator.main import app


@pytest.fixture(name="client")
async def client_():
    """Создает изолированный HTTP-клиент с полной инициализацией жизненного цикла FastAPI."""
    async with LifespanManager(app) as manager:
        transport = ASGITransport(app=manager.app)

        async with AsyncClient(
            transport=transport,
            base_url="http://test",
        ) as client:
            yield client


@pytest.fixture
async def workflow_request():
    """Возвращает валидную структуру данных для тестирования запуска воркфлоу."""
    return {
        "user_input": (
            "What is retrieval augmented generation "
            "and what are its main benefits?"
        ),
        "max_iterations": 5,
    }


@pytest.fixture
def run_orchestrator(client):
    """Фабрика для удобного выполнения POST-запросов к оркестратору в тестах."""
    async def _run(user_input="What is RAG?", max_iterations=2):
        response = await client.post(
            "/api/v1/workflows/run",
            json={
                "user_input": user_input,
                "max_iterations": max_iterations,
            },
        )
        return response
    return _run
