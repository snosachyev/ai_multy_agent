"""Модуль для расчета метрик оркестратора.

Предоставляет функции для извлечения статистических данных (количества итераций,
вызовов агентов, ошибок) из результатов выполнения, а также вспомогательные
утилиты для агрегации метрик.
"""

from __future__ import annotations


def task_completion(result: dict) -> float:
    """
    1.0 if workflow produced a final answer without errors.
    0.0 otherwise.
    """

    final_answer = result.get("final_answer")
    errors = result.get("errors") or []

    if final_answer and not errors:
        return 1.0

    return 0.0


def workflow_completed(result: dict) -> float:
    """
    Checks that workflow reached the final stage.
    """

    final_answer = result.get("final_answer")

    return 1.0 if final_answer else 0.0


def agent_execution_success_rate(result: dict) -> float:
    """
    Percentage of successfully executed specialized agents.
    """

    agent_results = result.get("agent_results") or []

    if not agent_results:
        return 0.0

    successful = sum(
        1
        for item in agent_results
        if item.get("success") is True
    )

    return successful / len(agent_results)


def routing_success(result: dict) -> float:
    """
    Basic orchestration routing health metric.

    For now, routing is considered successful when:
    - at least one specialized agent was executed;
    - no agent execution errors occurred;
    - workflow produced a final answer.

    This is not routing accuracy against an expected route.
    True routing accuracy can be added later using
    expected_agents from the evaluation dataset.
    """

    agent_results = result.get("agent_results") or []
    errors = result.get("errors") or []
    final_answer = result.get("final_answer")

    if not agent_results:
        return 0.0

    if errors:
        return 0.0

    if not final_answer:
        return 0.0

    return 1.0


def iterations(result: dict) -> int:
    """Возвращает количество итераций, выполненных оркестратором.

    Args:
        result: Словарь с результатами выполнения оркестратора.

    Returns:
        Количество итераций. Если ключ "iteration" отсутствует или равен None,
        возвращает 0.
    """
    return int(result.get("iteration") or 0)


def agent_calls(result: dict) -> int:
    """Подсчитывает общее количество вызовов агентов.

    Args:
        result: Словарь с результатами выполнения оркестратора.

    Returns:
        Количество вызовов агентов на основе длины списка "agent_results".
        Если список пуст или отсутствует, возвращает 0.
    """
    return len(result.get("agent_results") or [])


def errors_count(result: dict) -> int:
    """Подсчитывает количество ошибок, возникших в процессе работы.

    Args:
        result: Словарь с результатами выполнения оркестратора.

    Returns:
        Количество зафиксированных ошибок на основе длины списка "errors".
        Если список пуст или отсутствует, возвращает 0.
    """
    return len(result.get("errors") or [])


def average(values: list[float]) -> float:
    """Вычисляет среднее арифметическое списка числовых значений.

    Args:
        values: Список чисел с плавающей точкой (или целых чисел).

    Returns:
        Среднее значение в виде float. Если список пуст, возвращает 0.0.
    """
    if not values:
        return 0.0
    return sum(values) / len(values)
