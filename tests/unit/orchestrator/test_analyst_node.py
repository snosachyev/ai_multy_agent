"""Модульные тесты для проверки работы узла аналитика (analyst_node) в оркестраторе воркфлоу."""

from unittest.mock import AsyncMock, Mock

import pytest

from rag_platform_orchestrator.application.workflow import Workflow


@pytest.fixture
def _workflow_fixture():
    """Фикстура для инициализации экземпляра Workflow с заглушками (Mock) вместо реальных агентов.

    Returns:
        Workflow: Тестируемый объект оркестратора с моками агентов.
    """
    director = Mock()
    researcher = Mock()
    analyst = Mock()
    finalizer = Mock()

    return Workflow(
        director=director,
        researcher=researcher,
        analyst=analyst,
        finalizer=finalizer,
    )


@pytest.mark.anyio
async def test_analyst_node_success(_workflow_fixture, make_state):
    """Проверяет успешное выполнение задачи аналитиком и корректное обновление состояния."""
    _workflow_fixture.analyst.execute = AsyncMock(
        return_value=Mock(
            success=True,
            result={"result": "Анализ найденной информации."},
            error=None,
        )
    )

    state = make_state(
        next_action="analyst",
        iteration=1,
        max_iterations=5,
    )

    result = await _workflow_fixture.analyst_node(state)

    assert result["analysis_result"] == "Анализ найденной информации."

    assert result["last_action"] == "analyst"
    assert result["last_agent_success"] is True
    assert result["last_error"] is None
    assert result["iteration"] == 2

    assert len(result["agent_results"]) == 1
    assert result["agent_results"][0]["agent"] == "analyst"
    assert result["agent_results"][0]["success"] is True


@pytest.mark.anyio
async def test_analyst_node_failure(_workflow_fixture, make_state):
    """Проверяет обработку ошибок (RuntimeError) при падении агента-аналитика."""
    _workflow_fixture.analyst.execute = AsyncMock(
        side_effect=RuntimeError("Analyst unavailable")
    )

    state = make_state(
        next_action="analyst",
        iteration=1,
        max_iterations=5,
    )

    result = await _workflow_fixture.analyst_node(state)

    assert result["last_action"] == "analyst"
    assert result["last_agent_success"] is False

    assert "Analyst unavailable" in result["last_error"]

    assert len(result["errors"]) == 1
    assert "Analyst unavailable" in result["errors"][0]

    assert len(result["agent_results"]) == 1
    assert result["agent_results"][0]["agent"] == "analyst"
    assert result["agent_results"][0]["success"] is False

    assert result["iteration"] == 2


@pytest.mark.anyio
async def test_analyst_node_receives_research_result(_workflow_fixture, make_state):
    """Проверяет, что аналитику на вход передаются правильные аргументы из текущего состояния."""
    _workflow_fixture.analyst.execute = AsyncMock(
        return_value=Mock(
            success=True,
            result={"result": "Анализ"},
            error=None,
        )
    )

    state = make_state(
        next_action="analyst",
        iteration=0,
        max_iterations=5,
    )
    await _workflow_fixture.analyst_node(state)

    _workflow_fixture.analyst.execute.assert_called_once_with(
        user_input="Что такое RAG?",
        workflow_id="test-workflow",
        task="Проанализируй найденную информацию",
        research_result="RAG — это Retrieval Augmented Generation.",
    )
