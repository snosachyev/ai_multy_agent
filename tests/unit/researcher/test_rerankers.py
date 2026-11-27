"""Юнит-тесты для реранкеров и фильтрации по источникам в RAGService."""
from unittest.mock import AsyncMock, Mock

import pytest

from rag_platform_researcher.application.rag import RAGService
from rag_platform_researcher.infrastructure.rag.rerankers import RRFReranker


@pytest.mark.anyio
async def test_rrf_reranker_boosts_overlapping_documents():
    """Проверяет, что RRF поднимает на 1-е место документ, найденный по нескольким подзапросам."""
    reranker = RRFReranker(k=60)

    # Подзапрос 1: doc-A на 1-м месте, doc-B на 2-м
    query_1_results = [
        {"id": "doc-A", "content": "Текст A", "metadata": {}},
        {"id": "doc-B", "content": "Текст B", "metadata": {}},
    ]
    # Подзапрос 2: doc-C на 1-м месте, doc-B снова на 2-м
    query_2_results = [
        {"id": "doc-C", "content": "Текст C", "metadata": {}},
        {"id": "doc-B", "content": "Текст B", "metadata": {}},
    ]

    ranked = await reranker.rerank(
        query="Тестовый вопрос",
        search_results=[query_1_results, query_2_results],
        top_k=2,
    )

    # doc-B встретился в обоих списках, поэтому его итоговый RRF-скор выше всех
    assert len(ranked) == 2
    assert ranked[0]["id"] == "doc-B"


@pytest.mark.anyio
async def test_rag_service_passes_source_ids_to_vector_store():
    """Проверяет, что RAGService передает source_ids в каждый вызов vector_store.search."""
    mock_vector_store = AsyncMock()
    mock_vector_store.search.return_value = [
        {
            "id": "alice-0002",
            "content": "Чеширский Кот умел постепенно исчезать.",
            "metadata": {"source_id": "alice-in-wonderland"},
        }
    ]

    mock_query_generator = AsyncMock()
    mock_query_generator.generate.return_value = ["Кто такой Чеширский Кот?"]

    mock_llm = AsyncMock()
    mock_llm.ainvoke.return_value = Mock(content="Кот умел исчезать, оставляя улыбку.")

    service = RAGService(
        vector_store=mock_vector_store,
        query_generator=mock_query_generator,
        reranker=RRFReranker(),
        llm=mock_llm,
    )

    result = await service.execute(
        task="Кто такой Чеширский Кот?",
        source_ids=["alice-in-wonderland"],
    )

    mock_vector_store.search.assert_called_once_with(
        query="Кто такой Чеширский Кот?",
        limit=5,
        source_ids=["alice-in-wonderland"],
    )
    assert result.documents[0].id == "alice-0002"
