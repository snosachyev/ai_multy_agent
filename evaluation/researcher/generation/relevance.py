"""Модуль для оценки релевантности (relevance) ответа RAG-системы исходному вопросу."""

import json
from typing import Any, Dict

# Текст промпта скрыт внутри модуля и очищен от лишних пробелов
_RELEVANCE_PROMPT = """
You are evaluating whether a RAG answer actually answers the question.

Return ONLY valid JSON:

{
  "score": 0.0,
  "reason": "short explanation"
}

Score:
1.0 = directly answers the question
0.5 = partially answers the question
0.0 = does not answer the question
"""


async def evaluate_relevance(
    llm: Any,
    question: str,
    answer: str,
) -> Dict[str, Any]:
    """Оценивает, насколько сгенерированный ответ соответствует заданному вопросу.

    Функция проверяет, отвечает ли модель по существу на поставленный вопрос,
    независимо от того, содержит ли ответ фактические ошибки (для этого служат
    другие метрики). Запрос отправляется асинхронно.

    Args:
        llm: Объект языковой модели (судья), поддерживающий асинхронный метод `ainvoke`.
        question: Исходный вопрос пользователя.
        answer: Сгенерированный RAG-системой ответ, релевантность которого проверяется.

    Returns:
        Dict[str, Any]: Словарь с результатами оценки.
        При успешном парсинге содержит ключи:
            - "score" (float): Оценка релевантности (1.0, 0.5 или 0.0).
            - "reason" (str): Краткое обоснование оценки судьей.
        При ошибках интеграции или парсинга возвращает дефолтный словарь.
    """
    prompt = f"""
    {_RELEVANCE_PROMPT.strip()}

    QUESTION:
    {question}

    ANSWER:
    {answer}
    """.strip()

    try:
        # Шаг 1: Вызов LLM. Ловим только интерфейсные или сетевые исключения
        try:
            response = await llm.ainvoke(prompt)
        except (AttributeError, RuntimeError) as e:
            return {
                "score": 0.0,
                "reason": f"LLM invocation failed: {e}",
            }

        # Безопасное извлечение строкового контента
        content = getattr(response, "content", response)

        if not isinstance(content, str):
            return {
                "score": 0.0,
                "reason": f"Judge returned unexpected response type: {type(content).__name__}",
            }

        # Очистка от возможных Markdown-оберток (```json ... ```)
        cleaned_content = content.strip().removeprefix("```json").removesuffix("```").strip()

        # Шаг 2: Парсинг JSON. Ловим исключительно JSONDecodeError
        return json.loads(cleaned_content)

    except json.JSONDecodeError as e:
        return {
            "score": 0.0,
            "reason": f"Judge returned invalid JSON: {e.msg} at line {e.lineno} col {e.colno}",
        }
