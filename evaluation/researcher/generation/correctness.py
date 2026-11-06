"""Модуль для оценки фактической точности ответов RAG-системы с помощью LLM."""

import json
from typing import Any, Dict

_CORRECTNESS_PROMPT = """
You are evaluating the factual correctness of a RAG answer.

Compare the generated answer with the reference answer.

The generated answer does not need to use the exact same wording.
Equivalent meaning is acceptable.

Return ONLY valid JSON:

{
  "score": 0.0,
  "reason": "short explanation"
}

Score:
1.0 = correct
0.5 = partially correct
0.0 = incorrect
"""


async def evaluate_correctness(
    llm: Any,
    question: str,
    reference_answer: str,
    answer: str,
) -> Dict[str, Any]:
    """Оценивает фактическую точность сгенерированного ответа RAG по сравнению с эталоном.

    Функция отправляет асинхронный запрос к LLM (судье) с промптом, содержащим
    исходный вопрос, эталонный ответ и сгенерированный ответ. Ожидается, что
    модель вернет строго структурированный JSON с оценкой и объяснением.

    Args:
        llm: Объект языковой модели (например, из langchain), поддерживающий
            асинхронный метод `ainvoke`.
        question: Исходный вопрос пользователя.
        reference_answer: Идеальный (эталонный) ответ.
        answer: Ответ, сгенерированный RAG-системой, который нужно оценить.

    Returns:
        Dict[str, Any]: Словарь с результатами оценки.
        При успешном парсинге содержит ключи:
            - "score" (float): Оценка корректности (1.0, 0.5 или 0.0).
            - "reason" (str): Краткое обоснование оценки.
        В случае ошибки парсинга или вызова модели возвращает дефолтный словарь.
    """
    prompt = f"""
    {_CORRECTNESS_PROMPT.strip()}

    QUESTION:
    {question}

    REFERENCE ANSWER:
    {reference_answer}

    GENERATED ANSWER:
    {answer}
    """.strip()

    try:
        # 1. Шаг вызова LLM. Ловим возможные ошибки интерфейса (например, отсутствие ainvoke)
        # или сетевые ошибки провайдера, если они наследуются от стандартных 
        # (например, RuntimeError)
        try:
            response = await llm.ainvoke(prompt)
        except (AttributeError, RuntimeError) as e:
            return {
                "score": 0.0,
                "reason": f"LLM invocation failed: {e}",
            }

        # Извлекаем контент (если это объект AIMessage, берем .content, иначе как строку)
        content = getattr(response, "content", response)

        if not isinstance(content, str):
            return {
                "score": 0.0,
                "reason": f"Judge returned unexpected response type: {type(content).__name__}",
            }

        # Очищаем от возможных Markdown-оберток (```json ... ```)
        cleaned_content = content.strip().removeprefix("```json").removesuffix("```").strip()

        # 2. Шаг парсинга JSON. Ловим исключительно JSONDecodeError
        return json.loads(cleaned_content)

    except json.JSONDecodeError as e:
        return {
            "score": 0.0,
            "reason": f"Judge returned invalid JSON: {e.msg} at line {e.lineno} col {e.colno}",
        }
