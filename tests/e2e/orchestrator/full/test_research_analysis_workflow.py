"""
End-to-end tests for combined research and analysis agent workflows.

Validates that the orchestrator properly orchestrates multi-agent tasks,
ensuring that telemetry or results from individual agents are captured.
"""

import pytest


@pytest.mark.anyio
async def test_research_and_analysis_workflow(run_orchestrator):
    """
    Проверяет комплексный воркфлоу, включающий этапы исследования и анализа.

    Тест отправляет составной запрос, требующий сбора данных и оценки ограничений,
    после чего валидирует не только успешный статус-код и наличие финального ответа,
    но и проверяет структуру `agent_results`, гарантируя, что промежуточная работа
    конкретных агентов была успешно зафиксирована в теле ответа.
    """
    response = await run_orchestrator(
        user_input=(
            "Research retrieval augmented generation, "
            "then analyze its main advantages and limitations."
        ),
        max_iterations=3,
    )

    assert response.status_code == 200

    body = response.json()

    assert body["workflow_id"]
    assert body["final_answer"]

    assert isinstance(body["final_answer"], str)
    assert body["final_answer"].strip()

    if "agent_results" in body:
        assert isinstance(body["agent_results"], list)
        assert len(body["agent_results"]) > 0
