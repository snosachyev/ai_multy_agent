"""Общие фикстуры и инструменты для тестирования оркестратора воркфлоу."""

from unittest.mock import Mock, AsyncMock, MagicMock

import pytest

from rag_platform_orchestrator.application.workflow import Workflow


@pytest.fixture
def make_state():
    """Фабрика для генерации и гибкой настройки состояния (State) воркфлоу.

    Returns:
        callable: Функция, принимающая любые именованные аргументы (kwargs)
            для переопределения стандартных полей состояния.
    """
    def _make_state(**kwargs):
        base_state = {
            "workflow_id": "test-workflow",
            "user_input": "Что такое RAG?",
            "current_agent": None,
            "current_task": "Проанализируй найденную информацию",
            "next_action": "researcher",
            "iteration": 0,
            "max_iterations": 5,
            "research_result": "RAG — это Retrieval Augmented Generation.",
            "analysis_result": None,
            "agent_results": [],
            "completed_tasks": None,
            "last_action": "researcher",
            "last_agent_success": True,
            "last_error": None,
            "errors": [],
            "final_answer": None,
        }
        # Перезаписываем дефолтные поля теми, что передали в тест
        base_state.update(kwargs)
        return base_state

    return _make_state


@pytest.fixture(name="workflow_fixture")
def _workflow_fixture_impl():
    """Фикстура воркфлоу с правильными асинхронными моками."""
    # Все агенты ДОЛЖНЫ быть AsyncMock, иначе граф упадет на await
    director = AsyncMock()
    researcher = AsyncMock()
    analyst = AsyncMock()
    finalizer = AsyncMock()

    return Workflow(
        director=director,
        researcher=researcher,
        analyst=analyst,
        finalizer=finalizer,
    )


@pytest.fixture
def setup_happy_path():
    """Фикстура-помощник для быстрой настройки успешного прохождения всех агентов."""
    def _setup(workflow_fixture):
        # Настройка директора
        workflow_fixture.director.decide.side_effect = [
            MagicMock(next_action="researcher", task="Найди информацию о RAG"),
            MagicMock(next_action="analyst", task="Проанализируй информацию"),
            MagicMock(next_action="finish", task=None),
        ]

        # Настройка исследователя
        researcher_response = Mock(
            success=True,
            task="Найди информацию о RAG",
            error=None,
            result={"success": True, "result": {"answer": "Результат исследования."}}
        )
        workflow_fixture.researcher.execute.return_value = researcher_response

        # Настройка аналитика
        analyst_response = Mock(
            success=True,
            task="Проанализируй информацию",
            error=None,
            result={"success": True, "result": {"answer": "Результат анализа."}}
        )
        workflow_fixture.analyst.execute.return_value = analyst_response

        # Настройка финализатора
        workflow_fixture.finalizer.execute.return_value = "Финальный ответ."

    return _setup
