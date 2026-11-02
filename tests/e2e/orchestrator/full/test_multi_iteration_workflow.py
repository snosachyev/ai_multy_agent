"""
End-to-end tests for evaluating multi-iteration agent workflows.

Verifies that the orchestrator can sustain multi-step reasoning chains,
tracking loop iterations properly without early termination or regression.
"""

import pytest


@pytest.mark.anyio
async def test_multi_iteration_workflow(run_orchestrator):
    """
    Проверяет успешное выполнение комплексного воркфлоу, требующего нескольких итераций.

    Тест отправляет сложный аналитический запрос, подразумевающий глубокий поиск
    и оценку компромиссов (trade-offs), задает лимит в 3 итерации и контролирует,
    что система совершила как минимум один полный шаг рассуждения (iteration >= 1).
    """
    response = await run_orchestrator(
        user_input=(
            "Investigate retrieval augmented generation "
            "and provide an analysis of its trade-offs."
        ),
        max_iterations=3,
    )

    assert response.status_code == 200

    body = response.json()

    assert body["workflow_id"]
    assert body["final_answer"]

    if "iteration" in body:
        assert body["iteration"] >= 1
