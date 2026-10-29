"""
Metrics evaluation utilities for the researcher component.

Provides helper functions to extract, clean, and calculate aggregate
statistical performance indicators from agent execution results.
"""


def average(results: list[dict], key: str) -> float:
    """
    Вычисляет среднее арифметическое значение для указанного ключа из списка результатов.

    Функция обходит список словарей, безопасно извлекает числовые значения по ключу
    (поддерживает как прямые числа, так и вложенные структуры вида `{"score": value}`),
    игнорирует пропущенные или некорректные данные и возвращает итоговое среднее.

    Args:
        results: Список словарей с сырыми результатами работы агента.
        key: Название ключа, по которому нужно рассчитать метрику.

    Returns:
        Среднее значение метрики в формате float. Возвращает 0.0, если список
        результатов пуст или не удалось извлечь ни одного числового значения.
    """
    if not results:
        return 0.0

    values = []

    for result in results:
        value = result.get(key)

        if value is None:
            continue

        if isinstance(value, dict):
            score = value.get("score")

            if score is None:
                continue

            values.append(float(score))
        else:
            values.append(float(value))

    if not values:
        return 0.0

    return sum(values) / len(values)
