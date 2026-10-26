"""Общие фикстуры и инструменты для тестирования оркестратора воркфлоу."""

from unittest.mock import Mock, AsyncMock

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


@pytest.fixture
def workflow_fixture():
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
