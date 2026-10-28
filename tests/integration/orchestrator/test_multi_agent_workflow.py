"""Интеграционные тесты для проверки сквозного многоагентного воркфлоу (Multi-Agent Workflow)."""

from unittest.mock import MagicMock, Mock

import pytest


@pytest.mark.anyio
async def test_researcher_to_analyst_to_finalizer(workflow_fixture):
    """Проверяет последовательную цепочку переходов: 
    Директор -> Исследователь -> Аналитик -> Финализатор.

    Тест контролирует наполнение всех полей результирующего состояния (State), включая
    накопление истории в agent_results, технические флаги, итерации и финальные ответы.
    """
    # 1. Настраиваем последовательные ответы директора
    response_to_researcher = MagicMock(next_action="researcher", task="Найди информацию о RAG")
    response_to_analyst = MagicMock(next_action="analyst", task="Проанализируй информацию")
    response_to_finish = MagicMock(next_action="finish", task=None)

    workflow_fixture.director.decide.side_effect = [
        response_to_researcher,
        response_to_analyst,
        response_to_finish,
    ]

    # 2. Настраиваем исследователя
    researcher_response = Mock()
    researcher_response.success = True
    researcher_response.task = "Найди информацию о RAG"
    researcher_response.error = None
    researcher_response.result = {
        "success": True,
        "result": {"answer": "Результат исследования."},
    }
    workflow_fixture.researcher.execute.return_value = researcher_response

    # 3. Настраиваем аналитика
    analyst_response = Mock()
    analyst_response.success = True
    analyst_response.task = "Проанализируй информацию"
    analyst_response.error = None
    analyst_response.result = {
        "success": True,
        "result": {"answer": "Результат анализа."},
    }
    workflow_fixture.analyst.execute.return_value = analyst_response

    # 4. Настраиваем финализатора
    workflow_fixture.finalizer.execute.return_value = "Финальный ответ."

    # Запуск сквозного сценария
    result = await workflow_fixture.run(
        user_input="Что такое RAG?",
        max_iterations=5,
    )

    # === Проверки контента ответов в стейте ===
    assert result["research_result"] == "Результат исследования."
    # аналитик сохраняет структуру словаря
    assert result["analysis_result"] == {"answer": "Результат анализа."}
    assert result["final_answer"] == "Финальный ответ."

    # === Глубокие проверки метаданных и флагов стейта ===
    assert len(result["agent_results"]) == 2

    # берем первый элемент списка, так как это список (list)
    researcher_history = result["agent_results"][0]
    assert researcher_history["agent"] == "researcher"
    assert researcher_history["success"] is True
    assert researcher_history["task"] == "Найди информацию о RAG"
    assert researcher_history["result"]["success"] is True

    # При желании можно также проверить и второй элемент — аналитика:
    analyst_history = result["agent_results"][1]
    assert analyst_history["agent"] == "analyst"
    assert analyst_history["success"] is True


    # Проверки счетчиков вызовов моков
    assert workflow_fixture.director.decide.call_count == 3
    assert workflow_fixture.researcher.execute.call_count == 1
    assert workflow_fixture.analyst.execute.call_count == 1
    assert workflow_fixture.finalizer.execute.call_count == 1


@pytest.mark.anyio
async def test_research_result_is_passed_to_analyst(workflow_fixture, setup_happy_path):
    """Проверяет, что результаты работы исследователя корректно 
    передаются аналитику в качестве аргументов."""
    setup_happy_path(workflow_fixture)

    await workflow_fixture.run(user_input="Что такое RAG?", max_iterations=5)

    # Получаем kwargs вызова аналитика
    _, analyst_kwargs = workflow_fixture.analyst.execute.call_args
    assert analyst_kwargs["research_result"] == "Результат исследования."
    assert analyst_kwargs["workflow_id"] is not None
    assert analyst_kwargs["user_input"] == "Что такое RAG?"


@pytest.mark.anyio
async def test_research_and_analysis_results_are_passed_to_finalizer(workflow_fixture):
    """Проверяет, что накопленные результаты (поиск + анализ)
    корректно передаются на вход финализатору."""
    workflow_fixture.director.decide.side_effect = [
        MagicMock(next_action="researcher", task="Найди информацию о RAG"),
        MagicMock(next_action="analyst", task="Проанализируй информацию"),
        MagicMock(next_action="finish", task=None),
    ]

    researcher_response = Mock()
    researcher_response.success = True
    researcher_response.task = "Найди информацию о RAG"
    researcher_response.error = None
    researcher_response.result = {
        "success": True,
        "result": {"answer": "Результат исследования."},
    }
    workflow_fixture.researcher.execute.return_value = researcher_response

    analyst_response = Mock()
    analyst_response.success = True
    analyst_response.task = "Проанализируй информацию"
    analyst_response.error = None
    analyst_response.result = {
        "success": True,
        "result": {"answer": "Результат анализа."},
    }
    workflow_fixture.analyst.execute.return_value = analyst_response

    workflow_fixture.finalizer.execute.return_value = "Финальный ответ."

    await workflow_fixture.run(user_input="Что такое RAG?", max_iterations=5)

    # Получаем kwargs вызова финализатора
    _, finalizer_kwargs = workflow_fixture.finalizer.execute.call_args
    assert finalizer_kwargs["research_result"] == "Результат исследования."
    # проверяем переданную структуру словаря вместо строки
    assert finalizer_kwargs["analysis_result"] == {"answer": "Результат анализа."}
    assert finalizer_kwargs["user_input"] == "Что такое RAG?"
