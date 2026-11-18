"""Адаптер векторного хранилища Qdrant"""
from typing import Any
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import AsyncQdrantClient, QdrantClient
from qdrant_client.http import models

from rag_platform_contracts.vector_store import EMBEDDING_MODEL_NAME
from rag_platform_researcher.application.rag import VectorStorePort


class QdrantVectorStoreAdapter(VectorStorePort):
    """Продакшн-поисковик по внешнему векторному хранилищу Qdrant."""

    def __init__(self, url: str, collection_name: str):
        self.collection_name = collection_name
        self.embeddings = HuggingFaceEmbeddings(
            model_name=EMBEDDING_MODEL_NAME,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )
        self._sync_client = QdrantClient(url=url)
        self._async_client = AsyncQdrantClient(url=url)

        self.vectorstore = QdrantVectorStore(
            client=self._sync_client,
            collection_name=collection_name,
            embedding=self.embeddings,
        )

    async def search(
        self,
        query: str,
        limit: int = 5,
        source_ids: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Выполняет асинхронный семантический поиск с фильтрацией по source_ids."""
        search_filter = None
        if source_ids:
            search_filter = models.Filter(
                must=[
                    models.FieldCondition(
                        key="metadata.source_id",
                        match=models.MatchAny(any=source_ids),
                    )
                ]
            )

        documents = await self.vectorstore.asimilarity_search(
            query=query,
            k=limit,
            filter=search_filter,
        )

        return [
            {
                "id": document.metadata.get("document_id", ""),
                "content": document.page_content,
                "metadata": document.metadata,
            }
            for document in documents
        ]

    async def get_available_sources(self) -> list[str]:
        """Запрашивает список доступных источников у порта хранилища."""
        records, _ = await self._async_client.scroll(
            collection_name=self.collection_name,
            with_payload=["metadata.source_id"],
            limit=1000,
        )
        sources = {
            r.payload.get("metadata", {}).get("source_id")
            for r in records
            if r.payload and "metadata" in r.payload
        }
        return sorted(list(filter(None, sources)))
