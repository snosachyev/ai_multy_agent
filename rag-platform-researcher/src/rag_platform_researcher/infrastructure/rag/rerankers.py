"""rerankers module"""
import asyncio
from typing import Any
from rag_platform_researcher.application.rag import RerankerPort
from sentence_transformers import CrossEncoder


class RRFReranker(RerankerPort):
    """Реранкер на основе алгоритма Reciprocal Rank Fusion (RRF)."""

    def __init__(self, k: int = 60):
        self.k = k  # Стандартная константа сглаживания для RRF

    async def rerank(
        self,
        query: str,
        search_results: list[list[dict[str, Any]]],
        top_k: int = 5,
    ) -> list[dict[str, Any]]:
        scores: dict[str, float] = {}
        docs_by_id: dict[str, dict[str, Any]] = {}

        for doc_list in search_results:
            for rank, doc in enumerate(doc_list):
                doc_id = doc["id"]
                docs_by_id[doc_id] = doc
                # Классическая формула RRF: 1 / (k + rank + 1)
                scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (self.k + rank + 1)

        # Сортируем ID по убыванию итогового балла RRF
        sorted_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)
        return [docs_by_id[doc_id] for doc_id in sorted_ids[:top_k]]


class CrossEncoderReranker(RerankerPort):
    """Нейросетевой реранкер на базе Cross-Encoder (BAAI/bge-reranker-base)."""

    def __init__(
        self,
        model_name: str = "BAAI/bge-reranker-v2-m3",
        device: str = "cpu",
    ):
        self.model = CrossEncoder(model_name, device=device)

    async def rerank(
        self,
        query: str,
        search_results: list[list[dict[str, Any]]],
        top_k: int = 5,
    ) -> list[dict[str, Any]]:
        # 1. Собираем уникальных кандидатов из всех подзапросов
        unique_docs: dict[str, dict[str, Any]] = {}
        for doc_list in search_results:
            for doc in doc_list:
                unique_docs[doc["id"]] = doc

        candidates = list(unique_docs.values())
        if not candidates:
            return []

        # 2. Формируем пары (вопрос, текст документа) для оценки
        pairs = [(query, doc["content"]) for doc in candidates]

        # 3. Запускаем тяжелый инференс в отдельном потоке, чтобы не блокировать FastAPI
        scores = await asyncio.to_thread(self.model.predict, pairs)

        # 4. Сортируем документы по оценке реранкера
        scored_docs = sorted(
            zip(candidates, scores),
            key=lambda x: float(x[1]),
            reverse=True,
        )
        return [doc for doc, _ in scored_docs[:top_k]]
