"""Модульные тесты для проверки логики маршрутизации (routing) внутри Workflow."""

from rag_platform_orchestrator.application.workflow import Workflow


def test_route_from_director_to_researcher(make_state):
    """Проверяет маршрутизацию от директора к исследователю (researcher)."""
    state = make_state(next_action="researcher")

    result = Workflow.route_from_director(state)

    assert result == "researcher"


def test_route_from_director_to_analyst(make_state):
    """Проверяет маршрутизацию от директора к аналитику (analyst)."""
    state = make_state(next_action="analyst")

    result = Workflow.route_from_director(state)

    assert result == "analyst"


def test_route_from_director_to_finish(make_state):
    """Проверяет маршрутизацию от директора на завершение воркфлоу (finish)."""
    state = make_state(next_action="finish")

    result = Workflow.route_from_director(state)

    assert result == "finish"


def test_route_from_director_to_finish_when_max_iterations_reached(make_state):
    """Проверяет принудительное завершение шагов, если достигнут лимит итераций."""
    state = make_state(
        next_action="researcher",
        iteration=5,
        max_iterations=5,
    )

    result = Workflow.route_from_director(state)

    assert result == "finish"


def test_route_after_successful_agent_to_director(make_state):
    """Проверяет возврат к директору после успешного выполнения задачи агентом."""
    state = make_state(last_agent_success=True)

    result = Workflow.route_after_agent(state)

    assert result == "director"


def test_route_after_failed_agent_to_finish(make_state):
    """Проверяет завершение воркфлоу в случае падения или ошибки агента."""
    state = make_state(last_agent_success=False)

    result = Workflow.route_after_agent(state)

    assert result == "finish"
