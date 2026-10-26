"""Модульные тесты для проверки работы финального узла (final_node) в оркестраторе воркфлоу."""

from unittest.mock import AsyncMock

import pytest


@pytest.mark.anyio
async def test_final_node_returns_final_answer(workflow_fixture, make_state):
    """Проверяет, что финальный узел корректно сохраняет итоговый ответ в состояние воркфлоу.

    Тест контролирует, что возвращенное финализатором строковое значение записывается
    в поле final_answer результирующего состояния.
    """
    workflow_fixture.finalizer.execute = AsyncMock(
        return_value="Итоговый ответ."
    )

    state = make_state(
        current_task=None,
        next_action="finish",
        iteration=2,
        analysis_result="RAG объединяет поиск документов и генерацию ответа.",
        last_action="analyst",
    )

    result = await workflow_fixture.final_node(state)

    assert result["final_answer"] == "Итоговый ответ."


@pytest.mark.anyio
async def test_final_node_passes_results_to_finalizer(workflow_fixture, make_state):
    """Проверяет корректность передачи накопленного контекста в метод execute финализатора.

    Тест гарантирует, что агрегированные результаты поиска (research_result)
    и анализа (analysis_result) из состояния правильно маппятся в аргументы вызова.
    """
    workflow_fixture.finalizer.execute = AsyncMock(
        return_value="Итоговый ответ."
    )

    state = make_state(
        current_task=None,
        next_action="finish",
        iteration=2,
        analysis_result="RAG объединяет поиск документов и генерацию ответа.",
        last_action="analyst",
    )

    await workflow_fixture.final_node(state)

    workflow_fixture.finalizer.execute.assert_called_once_with(
        workflow_id="test-workflow",
        user_input="Что такое RAG?",
        research_result="RAG — это Retrieval Augmented Generation.",
        analysis_result="RAG объединяет поиск документов и генерацию ответа.",
    )
