"""Общие фикстуры и инструменты для тестирования оркестратора воркфлоу."""

from unittest.mock import Mock

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
