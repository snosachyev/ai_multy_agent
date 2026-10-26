"""Модульные тесты для проверки работы узла исследователя (researcher_node) 
в оркестраторе воркфлоу."""

from unittest.mock import AsyncMock, Mock

import pytest


@pytest.mark.anyio
async def test_researcher_node_success(workflow_fixture, make_state):
    """Проверяет успешное выполнение поиска информации исследователем.

    Тест контролирует, что результат поиска корректно записывается в поле
    research_result, а также обновляются метаданные о последнем шаге и итерации.
    """
    workflow_fixture.researcher.execute = AsyncMock(
        return_value=Mock(
            success=True,
            result={
                "success": True,
                "result": {
                    "answer": "RAG — это Retrieval Augmented Generation.",
                },
            },
            error=None,
        )
    )

    state = make_state(
        current_task="Что такое RAG?",
        research_result=None,
        last_action=None,
        last_agent_success=None
    )

    result = await workflow_fixture.researcher_node(state)

    assert (
        result["research_result"]
        == "RAG — это Retrieval Augmented Generation."
    )

    assert result["last_action"] == "researcher"
    assert result["last_agent_success"] is True
    assert result["last_error"] is None
    assert result["iteration"] == 1

    assert len(result["agent_results"]) == 1
    assert result["agent_results"][0]["agent"] == "researcher"
    assert result["agent_results"][0]["success"] is True


@pytest.mark.anyio
async def test_researcher_node_failure(workflow_fixture, make_state):
    """Проверяет обработку исключений (RuntimeError) при сбое в работе исследователя.

    Тест контролирует, что при падении агента воркфлоу не завершается аварийно,
    а корректно логирует ошибку в списки last_error и errors текущего состояния.
    """
    workflow_fixture.researcher.execute = AsyncMock(
        side_effect=RuntimeError("Researcher unavailable")
    )

    state = make_state(
        current_task="Что такое RAG?",
        research_result=None,
        last_action=None,
        last_agent_success=None
    )

    result = await workflow_fixture.researcher_node(state)

    assert result["last_action"] == "researcher"
    assert result["last_agent_success"] is False

    assert "Researcher unavailable" in result["last_error"]

    assert len(result["errors"]) == 1
    assert "Researcher unavailable" in result["errors"][0]

    assert len(result["agent_results"]) == 1
    assert result["agent_results"][0]["agent"] == "researcher"
    assert result["agent_results"][0]["success"] is False

    assert result["iteration"] == 1


@pytest.mark.anyio
async def test_researcher_node_uses_current_task(workflow_fixture, make_state):
    """Проверяет корректность маппинга аргументов при вызове метода execute исследователя.

    Тест гарантирует, что узел передает в метод execute именно текущую задачу
    (current_task) из состояния, а не исходный пользовательский запрос.
    """
    workflow_fixture.researcher.execute = AsyncMock(
        return_value=Mock(
            success=True,
            result={
                "success": True,
                "result": {
                    "answer": "Ответ",
                },
            },
            error=None,
        )
    )

    state = make_state(
        current_task="Что такое RAG?",
        research_result=None,
        last_action=None,
        last_agent_success=None
    )
    state["current_task"] = "Найди информацию о RAG"

    await workflow_fixture.researcher_node(state)

    workflow_fixture.researcher.execute.assert_called_once_with(
        workflow_id="test-workflow",
        user_input="Что такое RAG?",
        task="Найди информацию о RAG",
    )
