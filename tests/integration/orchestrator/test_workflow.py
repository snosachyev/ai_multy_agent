"""Интеграционные тесты для проверки базовых сквозных сценариев работы Workflow."""
import pytest


@pytest.mark.anyio
async def test_researcher_workflow(
    workflow_fixture,
    setup_happy_path,
):
    """Проверяет сквозной сценарий выполнения воркфлоу от сбора данных до финализации.

    Тест контролирует корректность прохождения шагов через Директора,
    Исследователя, Аналитика и Финализатора, а также проверяет наполнение
    ключевых полей ответов в результирующем состоянии.
    """

    setup_happy_path(workflow_fixture)

    result = await workflow_fixture.run(
        user_input="Что такое RAG?",
        max_iterations=5,
    )

    assert result["research_result"] == (
        "Результат исследования."
    )

    assert result["final_answer"] == "Финальный ответ."

    # Проверки счетчиков вызовов моков
    assert workflow_fixture.director.decide.call_count == 3
    assert workflow_fixture.researcher.execute.call_count == 1
    assert workflow_fixture.analyst.execute.call_count == 1
    assert workflow_fixture.finalizer.execute.call_count == 1
