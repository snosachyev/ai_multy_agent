"""Модуль тестов  проверки жизнеспособности процесса."""

import pytest


@pytest.mark.anyio
async def test_orchestrator_health(client):
    """Тест проверки жизнеспособности процесса."""
    response = await client.get("/health")

    assert response.status_code == 200
