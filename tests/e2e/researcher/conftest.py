"""
Fixtures and utilities for researcher e2e testing.

Provides initialized ASGI application clients, mock request payloads,
and helper factories to simulate workflow runs with full lifespan support.
"""

import pytest
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient

from rag_platform_researcher.main import app


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



