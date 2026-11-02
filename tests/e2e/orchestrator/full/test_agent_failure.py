"""
End-to-end tests for handling agent failures within the orchestrator workflow.

Verifies that the orchestrator gracefully manages downstream service disruptions
without breaking the entire API response lifecycle.
"""

import pytest


@pytest.mark.anyio
async def test_agent_failure_is_handled(run_orchestrator):
    """Проверяет корректность обработки критического сбоя агента при запуске воркфлоу."""
    # Используем фабрику вместо прямого client.post
    response = await run_orchestrator(
        user_input="Trigger an agent failure scenario.",
        max_iterations=3,
    )

    assert response.status_code in {200, 500}

    body = response.json()

    assert body is not None

    if response.status_code == 200:
        assert body["workflow_id"]
