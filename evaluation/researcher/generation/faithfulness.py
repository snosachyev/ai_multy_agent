"""Модуль для оценки обоснованности (faithfulness) ответа RAG-системы на основе контекста."""

import json
from typing import Any, Dict

# Текст промпта сделан скрытым константным полем и очищен от лишних табов/пробелов слева
_FAITHFULNESS_PROMPT = """
You are evaluating a RAG answer.

Your task is to determine whether the answer is fully supported
by the provided context.

Rules:
- Every factual claim in the answer must be supported by the context.
- Do not use outside knowledge.
- If the answer contains unsupported factual claims, it is not fully faithful.

Return ONLY valid JSON:

{
"score": 0.0,
"reason": "short explanation"
}

Score:
1.0 = fully supported
0.5 = partially supported
0.0 = unsupported
"""


async def evaluate_faithfulness(
    llm: Any,
    question: str,
    context: str,
    answer: str,
) -> Dict[str, Any]:
    """Оценивает, насколько сгенерированный ответ обоснован предоставленным контекстом.

    Функция проверяет галлюцинации: содержит ли ответ утверждения, которых нет в контексте.
    Запрос отправляется асинхронно в LLM, которая должна вернуть JSON с оценкой.

    Args:
        llm: Объект языковой модели (судья), поддерживающий асинхронный метод `ainvoke`.
        question: Исходный вопрос пользователя.
        context: Найденный контекст (фрагменты документов), переданный модели для генерации.
        answer: Сгенерированный RAG-системой ответ, который проверяется на галлюцинации.

    Returns:
        Dict[str, Any]: Словарь с результатами оценки.
        При успешном парсинге содержит ключи:
            - "score" (float): Оценка обоснованности (1.0, 0.5 или 0.0).
            - "reason" (str): Обоснование оценки судьей.
        При ошибках вызова или парсинга возвращает дефолтный словарь с описанием проблемы.
    """
    prompt = f"""
    {_FAITHFULNESS_PROMPT.strip()}

    QUESTION:
    {question}

    CONTEXT:
    {context}

    ANSWER:
    {answer}
    """.strip()

    try:
        # Ловим исключительно ошибки интерфейса или вызова LLM
        try:
            response = await llm.ainvoke(prompt)
        except (AttributeError, RuntimeError) as e:
            return {
                "score": 0.0,
                "reason": f"LLM invocation failed: {e}",
            }

        # Безопасно извлекаем текст ответа
        content = getattr(response, "content", response)

        if not isinstance(content, str):
            return {
                "score": 0.0,
                "reason": f"Judge returned unexpected response type: {type(content).__name__}",
            }

        # Очищаем от возможных Markdown-блоков кода (```json ... ```)
        cleaned_content = content.strip().removeprefix("```json").removesuffix("```").strip()

        return json.loads(cleaned_content)

    except json.JSONDecodeError as e:
        return {
            "score": 0.0,
            "reason": f"Judge returned invalid JSON: {e.msg} at line {e.lineno} col {e.colno}",
        }
