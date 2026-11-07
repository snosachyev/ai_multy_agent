"""Модуль для комплексной оценки качества генерации ответов RAG-системы.

Объединяет метрики обоснованности (faithfulness), релевантности (relevance)
и, при наличии эталона, фактической точности (correctness).
"""

import asyncio
from typing import Any, Dict, Optional

from evaluation.researcher.generation.correctness import evaluate_correctness
from evaluation.researcher.generation.faithfulness import evaluate_faithfulness
from evaluation.researcher.generation.relevance import evaluate_relevance

async def evaluate_generation(
    llm: Any,
    question: str,
    context: str,
    answer: str,
    reference_answer: Optional[str] = None,
) -> Dict[str, Any]:
    """Запускает комплексную оценку сгенерированного ответа по нескольким метрикам.

    Функция выполняет асинхронную оценку. Если передан `reference_answer`,
    все три метрики (faithfulness, relevance, correctness) вычисляются
    параллельно (конкурентно), что существенно сокращает общее время ожидания LLM.

    Args:
        llm: Объект языковой модели, используемый в качестве судьи.
        question: Исходный вопрос пользователя.
        context: Контекст (найденные документы/знания), на основе которого
            строился ответ.
        answer: Сгенерированный RAG-системой ответ, требующий оценки.
        reference_answer: Опциональный идеальный (эталонный) ответ.
            Если не передан, метрика `correctness` рассчитываться не будет.

    Returns:
        Dict[str, Any]: Словарь с результатами оценки по каждой метрике.
            Пример структуры:
            {
                "faithfulness": {"score": 1.0, "reason": "..."},
                "relevance": {"score": 0.5, "reason": "..."},
                "correctness": {"score": 1.0, "reason": "..."}  # Опционально
            }
    """
    # Формируем список базовых задач, которые выполняются всегда
    tasks = [
        evaluate_faithfulness(llm=llm, question=question, context=context, answer=answer),
        evaluate_relevance(llm=llm, question=question, answer=answer),
    ]

    # Если есть эталонный ответ, добавляем задачу оценки корректности
    if reference_answer:
        tasks.append(
            evaluate_correctness(
                llm=llm,
                question=question,
                reference_answer=reference_answer,
                answer=answer,
            )
        )

    # Запускаем все задачи конкурентно через asyncio.gather.
    # Это позволяет делать запросы к LLM параллельно, а не ждать их по очереди.
    results = await asyncio.gather(*tasks)

    # Собираем финальный словарь из результатов выполнения задач
    result_dict = {
        "faithfulness": results[0],
        "relevance": results[1],
    }

    if reference_answer:
        result_dict["correctness"] = results[2]

    return result_dict
