"""Модульные тесты для проверки структуры, топологии и состава узлов графа Workflow оркестратора."""

def test_workflow_contains_all_nodes(workflow_fixture):
    """Проверяет архитектуру графа и наличие в нём всех обязательных узлов (nodes).

    Тест гарантирует, что при сборке воркфлоу в граф были корректно добавлены
    все ключевые агенты и финальная точка завершения процесса.
    """
    graph = workflow_fixture.graph

    assert "director" in graph.nodes
    assert "researcher" in graph.nodes
    assert "analyst" in graph.nodes
    assert "finish" in graph.nodes
