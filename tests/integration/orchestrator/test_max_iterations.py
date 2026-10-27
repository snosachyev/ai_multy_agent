"""Интеграционные тесты для проверки лимитов итераций в Workflow оркестратора."""

from unittest.mock import Mock, MagicMock
import pytest

@pytest.mark.anyio
async def test_workflow_stops_at_max_iterations(workflow_fixture):
    """Проверяет принудительную остановку воркфлоу при достижении max_iterations.

    Тест контролирует, что граф делает переходы между узлами, честно наращивая
    счётчик итераций, пока не сработает лимит безопасности.
    """
    # 1. Создаем объекты ответов директора. Код в workflow.py читает их
    # через ТОЧКУ (decision.next_action)
    response1 = MagicMock()
    response1.next_action = "researcher"
    response1.task = "Повторное исследование 1"

    response2 = MagicMock()
    response2.next_action = "researcher"
    response2.task = "Повторное исследование 2"

    response3 = MagicMock()
    response3.next_action = "finish"
    response3.task = None

    # Настраиваем метод .decide (а не .execute), так как упало именно на нем
    workflow_fixture.director.decide.side_effect = [response1, response2, response3]

    # 2. Настраиваем исследователя. Его метод execute возвращает объект Mock
    workflow_fixture.researcher.execute.return_value = Mock(
        success=True,
        result={
            "success": True,
            "result": {"answer": "Результат исследования."},
        },
        error=None,
    )

    # 3. Настраиваем финализатор
    workflow_fixture.finalizer.execute.return_value = "Финальный ответ по лимиту."

    # Запускаем сквозной граф оркестратора
    result = await workflow_fixture.run(
        user_input="Что такое RAG?",
        max_iterations=2,
    )

    assert workflow_fixture.director.decide.call_count == 3
    assert workflow_fixture.researcher.execute.call_count == 2
    assert workflow_fixture.finalizer.execute.call_count == 1
    assert result["iteration"] >= 2
