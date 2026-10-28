"""Модуль интеграционного тестирования пайплайна RAGService.

Содержит тест-кейсы для проверки корректности сборки контекста,
взаимодействия с LLM и формирования финального ответа пользователю.
"""

from unittest.mock import AsyncMock, Mock
import pytest


@pytest.mark.anyio
async def test_rag_service_success_execution(rag_service):
    """Проверяет успешный базовый сценарий генерации ответа через RAG.
    
    Тест проверяет, что при корректных входных данных сервис успешно собирает
    документы из векторного хранилища и возвращает заполненную модель ответа.

    Args:
        rag_service: Фикстура тестируемого RAG-сервиса (инжектируется из conftest).
    """
    result = await rag_service.execute(
        task="Что такое RAG?"
    )

    assert result.answer == "Это тестовый ответ."
    assert result.documents


@pytest.mark.anyio
async def test_rag_service_llm_invocation_tracking(rag_service, mock_llm):
    """Проверяет строго однократный вызов языковой модели при работе пайплайна.
    
    Тест динамически переопределяет ответ LLM и верифицирует, что метод
    генерации текста (`ainvoke`) вызывается оркестратором ровно один раз.

    Args:
        rag_service: Фикстура тестируемого RAG-сервиса.
        mock_llm: Фикстура мока LLM для инспекции количества вызовов методов.
    """
    # Динамически меняем поведение мока под этот конкретный тест-кейс
    mock_llm.ainvoke = AsyncMock(
        return_value=Mock(content="Новый динамический ответ.")
    )

    result = await rag_service.execute(
        task="Что такое RAG?"
    )

    assert result.answer == "Новый динамический ответ."
    assert result.documents

    # Гарантируем отсутствие повторных или скрытых вызовов модели
    mock_llm.ainvoke.assert_called_once()
