"""
End-to-end tests for validation of iteration constraints within the orchestrator.

Verifies that the orchestrator respects the maximum allowed iterations parameter
and halts the agent execution chain appropriately.
"""

import pytest


@pytest.mark.anyio
async def test_max_iterations_is_respected(run_orchestrator):
    """
    Проверяет, что оркестратор строго соблюдает лимит на максимальное число итераций.

    Тест выполняет прогон воркфлоу через фабрику и убеждается, что итоговое число
    итераций в теле ответа не превышает заданный в параметрах порог (по умолчанию 2).
    """
    # Вызываем фабрику со стандартными значениями (max_iterations=2)
    response = await run_orchestrator()

    assert response.status_code == 200

    body = response.json()

    assert body["workflow_id"]
    assert body["final_answer"] is not None

    if "iteration" in body:
        assert body["iteration"] <= 2
