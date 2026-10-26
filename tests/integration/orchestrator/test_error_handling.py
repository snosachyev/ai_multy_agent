"""Модульные тесты для проверки механизмов обработки ошибок в Workflow оркестратора."""

from unittest.mock import AsyncMock

import pytest


@pytest.mark.anyio
async def test_analyst_failure_updates_state(workflow_fixture, make_state):
    """Проверяет, что при сбое аналитика узел корректно фиксирует ошибку в состоянии.

    Тест контролирует, что исключение RuntimeError перехватывается внутри analyst_node,
    а флаг выполнения last_agent_success переводится в положение False.
    """
    # Настраиваем Аналитика на симуляцию падения
    workflow_fixture.analyst.execute = AsyncMock(
        side_effect=RuntimeError("Analyst unavailable")
    )

    # ИСПРАВЛЕНИЕ: Передаем сгенерированный стейт в тестируемый узел
    state = make_state(
        next_action="analyst",
        iteration=1,
        max_iterations=5,
    )

    # Вызываем напрямую ноду, а не весь run
    result = await workflow_fixture.analyst_node(state)

    # Проверки измененного состояния
    assert result["last_agent_success"] is False

    assert result["errors"]
    assert "Analyst unavailable" in result["errors"][0]

    assert result["agent_results"]
    assert result["agent_results"][0]["agent"] == "analyst"
    assert result["agent_results"][0]["success"] is False

    assert workflow_fixture.analyst.execute.call_count == 1
