"""Модуль для расчета метрик ранжирования поисковой выдачи: 
Reciprocal Rank (RR) и Mean Reciprocal Rank (MRR)."""

from typing import List, Set, TypedDict


class QueryData(TypedDict):
    """Структура данных для одной поисковой сессии (запроса) в рамках оценки качества."""

    retrieved_ids: List[str]
    """Список идентификаторов документов, возвращенных поисковой 
    системой (в порядке релевантности)."""
    relevant_ids: List[str]
    """Список идентификаторов истинно релевантных документов (ground truth)."""


def reciprocal_rank(
    retrieved_ids: List[str],
    relevant_ids: List[str],
) -> float:
    """Вычисляет Reciprocal Rank (обратный ранг) для одного поискового запроса.

    Метрика определяет, насколько быстро пользователь находит первый релевантный документ.
    Если первый релевантный документ находится на позиции `N`, то RR равен `1/N`.
    Если ни один документ не совпал, возвращается `0.0`.

    Args:
        retrieved_ids: Список идентификаторов документов, возвращенных поисковой системой.
            Порядок элементов в списке принципиально важен 
            (от самых релевантных к менее релевантным).
        relevant_ids: Список идентификаторов документов, признанных релевантными.

    Returns:
        float: Значение обратного ранга в диапазоне [0.0, 1.0].
    """
    # Преобразуем в set для O(1) поиска внутри цикла, это ускоряет работу на больших списках
    relevant: Set[str] = set(relevant_ids)

    for rank, document_id in enumerate(retrieved_ids, start=1):
        if document_id in relevant:
            return 1.0 / rank

    return 0.0


def mean_reciprocal_rank(
    queries: List[QueryData],
) -> float:
    """Вычисляет Mean Reciprocal Rank (MRR) по всему набору тестовых запросов.

    Рассчитывает среднее значение Reciprocal Rank для всех переданных поисковых сессий.
    Если список запросов пуст, возвращается `0.0`.

    Args:
        queries: Список словарей, каждый из которых должен соответствовать структуре `QueryData`
            и содержать ключи "retrieved_ids" и "relevant_ids".

    Returns:
        float: Среднее значение MRR по всем запросам в диапазоне [0.0, 1.0].

    Raises:
        KeyError: Если в элементах списка отсутствуют обязательные ключи.
    """
    if not queries:
        return 0.0

    scores: List[float] = []
    for query in queries:
        # Рефакторинг: безопасное извлечение с понятной ошибкой, если структура данных нарушена
        try:
            score = reciprocal_rank(
                retrieved_ids=query["retrieved_ids"],
                relevant_ids=query["relevant_ids"],
            )
            scores.append(score)
        except KeyError as e:
            raise KeyError(
                f"""Invalid query format. Each query dictionary must contain 'retrieved_ids' and
                  'relevant_ids'. Missing key: {e}"""
            ) from e

    return sum(scores) / len(scores)
