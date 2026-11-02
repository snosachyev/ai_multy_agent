"""
Basic end-to-end integration tests for the orchestrator core workflow.

Verifies the successful execution path of standard requests, ensuring the 
system returns expected payload structures and generated answers.
"""

import pytest


@pytest.mark.anyio
async def test_basic_workflow(client, workflow_request):
    """
    Проверяет успешный базовый сценарий выполнения воркфлоу (happy path).

    Тест отправляет валидный запрос в оркестратор, проверяет успешный статус-код 200,
    а также валидирует структуру ответа: наличие идентификатора воркфлоу и 
    присутствие непустого текстового финального ответа.
    """
    response = await client.post(
        "/api/v1/workflows/run",
        json=workflow_request,
    )

    assert response.status_code == 200

    body = response.json()

    assert body["workflow_id"]
    assert body["final_answer"]

    assert isinstance(body["final_answer"], str)
    assert body["final_answer"].strip()
