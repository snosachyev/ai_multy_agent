"""Модуль для сравнения результатов двух прогонов оценки RAG-платформы.

Позволяет наглядно оценить изменение качества (метрики поиска и генерации)
после изменения конфигурации системы, промптов или моделей.
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

# Список базовых метрик для сравнения (раздел, базовое имя метрики)
METRICS: List[Tuple[str, str]] = [
    ("retrieval", "recall"),
    ("retrieval", "precision"),
    ("retrieval", "mrr"),
    ("generation", "faithfulness"),
    ("generation", "relevance"),
    ("generation", "correctness"),
]


def load_report(path: str) -> Dict[str, Any]:
    """Загружает JSON-отчет оценки с диска.

    Args:
        path (str): Путь к файлу отчета.

    Returns:
        Dict[str, Any]: Десериализованный словарь с данными отчета.
    """
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def get_metric(report: Dict[str, Any], section: str, metric_base: str) -> float:
    """Безопасно извлекает значение метрики из отчета с учетом динамических ключей.

    Автоматически адаптируется под динамические имена ключей ретривала,
    такие как 'recall_at_5' или 'precision_at_10', на основе конфигурации отчета.

    Args:
        report (Dict[str, Any]): Словарь отчета.
        section (str): Секция метрик ("retrieval" или "generation").
        metric_base (str): Базовое название метрики ("recall", "mrr", "faithfulness" и т.д.).

    Returns:
        float: Значение метрики. Если секция или метрика отсутствуют, возвращает 0.0.
    """
    summary = report.get("summary", {})
    section_data = summary.get(section, {})

    if not section_data:
        return 0.0

    # Рефакторинг: динамическое определение ключа для recall и precision
    if section == "retrieval" and metric_base in ("recall", "precision"):
        top_k = report.get("config", {}).get("top_k", 5)
        metric_key = f"{metric_base}_at_{top_k}"
    else:
        metric_key = metric_base

    return float(section_data.get(metric_key, 0.0))


def compare(before: Dict[str, Any], after: Dict[str, Any]) -> None:
    """Сравнивает два отчета и выводит красивую таблицу с дельтой изменений в консоль.

    Args:
        before (Dict[str, Any]): Отчет «до» изменений (базовый).
        after (Dict[str, Any]): Отчет «после» изменений.

    Returns:
        None
    """
    print()
    print("EVALUATION COMPARISON")
    print("=" * 80)

    # Выводим информацию о моделях для контекста
    model_before = before.get("config", {}).get("llm_model", "unknown")
    model_after = after.get("config", {}).get("llm_model", "unknown")
    print(f"Before LLM: {model_before}")
    print(f"After LLM:  {model_after}")
    print("-" * 80)

    print(
        f"{'Metric':<25}"
        f"{'Before':>12}"
        f"{'After':>12}"
        f"{'Delta':>12}"
    )

    print("-" * 80)

    for section, metric_base in METRICS:
        old = get_metric(before, section, metric_base)
        new = get_metric(after, section, metric_base)
        delta = new - old

        # Для вывода красивого имени метрики (например, с учетом K)
        if section == "retrieval" and metric_base in ("recall", "precision"):
            top_k = after.get("config", {}).get("top_k", 5)
            display_name = f"{metric_base}_at_{top_k}"
        else:
            display_name = metric_base

        print(
            f"{display_name:<25}"
            f"{old:>12.3f}"
            f"{new:>12.3f}"
            f"{delta:>+12.3f}"
        )
    print("=" * 80)


def main() -> None:
    """Главная управляющая функция для сравнения отчетов.

    Выполняет валидацию аргументов командной строки, проверяет физическое 
    существование файлов отчетов на диске, загружает их содержимое 
    и запускает процесс вычисления разницы (дельты) между прогонами.

    Raises:
        SystemExit: Если передано неверное количество аргументов 
            или указанные файлы не найдены.
    """
    if len(sys.argv) != 3:
        print("Usage: python compare_evaluations.py before.json after.json")
        sys.exit(1)

    # Проверяем переданные аргументы (индексы 1 и 2)
    if not Path(sys.argv[1]).exists() or not Path(sys.argv[2]).exists():
        print(f"""Error: One or both report files do not exist.\nPath 1:
                {sys.argv[1]}\nPath 2: {sys.argv[2]}""")
        sys.exit(1)

    before = load_report(sys.argv[1])
    after = load_report(sys.argv[2])

    compare(before, after)



if __name__ == "__main__":
    main()
