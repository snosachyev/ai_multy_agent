"""
Contracts validation tests for the orchestrator workflow API.

Ensures that the orchestrator response structures strictly adhere to the expected
JSON schema constraints, ensuring client compatibility.
"""

import pytest


@pytest.mark.anyio
async def test_workflow_response_contract(run_orchestrator):
    """
    Валидирует контракт JSON-ответа при успешном выполнении воркфлоу.

    Тест выполняет базовый запрос через фабрику и проверяет соответствие схемы:
    наличие всех обязательных полей (workflow_id, final_answer), а также
    типы данных этих полей и их корректную заполненность.
    """
    response = await run_orchestrator()

    assert response.status_code == 200

    body = response.json()

    required_fields = {
        "workflow_id",
        "final_answer",
    }

    # Проверяем, что все обязательные поля присутствуют в ответе
    assert required_fields.issubset(body.keys())

    # Проверка формата workflow_id
    assert isinstance(body["workflow_id"], str)
    assert body["workflow_id"]

    # Проверка формата final_answer
    assert isinstance(body["final_answer"], str)
    assert body["final_answer"].strip()
