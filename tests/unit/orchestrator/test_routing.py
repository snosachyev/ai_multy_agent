"""Orchestrato routing test"""
from rag_platform_orchestrator.application.workflow import (
    Workflow,
)

def make_state(
    *,
    next_action="researcher",
    iteration=0,
    max_iterations=5,
    last_agent_success=True,
):
    return {
        "workflow_id": "test-workflow",
        "user_input": "Что такое RAG?",
        "current_agent": None,
        "current_task": None,
        "next_action": next_action,
        "iteration": iteration,
        "max_iterations": max_iterations,
        "research_result": None,
        "analysis_result": None,
        "agent_results": [],
        "completed_tasks": None,
        "last_action": None,
        "last_agent_success": last_agent_success,
        "last_error": None,
        "errors": [],
        "final_answer": None,
    }


def test_route_from_director_to_researcher():
    """test route from director to researcher"""
    state = make_state(next_action="researcher")

    result = Workflow.route_from_director(state)

    assert result == "researcher"


def test_route_from_director_to_analyst():
    state = make_state(next_action="analyst")

    result = Workflow.route_from_director(state)

    assert result == "analyst"


def test_route_from_director_to_finish():
    state = make_state(next_action="finish")

    result = Workflow.route_from_director(state)

    assert result == "finish"


def test_route_from_director_to_finish_when_max_iterations_reached():
    state = make_state(
        next_action="researcher",
        iteration=5,
        max_iterations=5,
    )

    result = Workflow.route_from_director(state)

    assert result == "finish"


def test_route_after_successful_agent_to_director():
    state = make_state(last_agent_success=True)

    result = Workflow.route_after_agent(state)

    assert result == "director"


def test_route_after_failed_agent_to_finish():
    state = make_state(last_agent_success=False)

    result = Workflow.route_after_agent(state)

    assert result == "finish"
