"""Поисковик хранилища ChromaDB"""
from typing import Any

import chromadb
from langchain_chroma import Chroma


from rag_platform_contracts.vector_store import (
    QDRANT_COLLECTION_NAME,
)
from rag_platform_researcher.application.rag import VectorStorePort
from rag_platform_researcher.infrastructure.rag.embeddings import get_embeddings

class ChromaVectorStore(
    VectorStorePort,
):
    """Класс поисковик векторного хранилища ChromaDB"""

    def __init__(
        self,
        host: str = "chroma",
        port: int = 8000,
        collection_name: str = QDRANT_COLLECTION_NAME,
    ):
        self.collection_name = collection_name

        self.embeddings = get_embeddings(device="cpu")

        self._client = chromadb.HttpClient(
            host=host,
            port=port,
        )

        self.vectorstore = Chroma(
            client=self._client,
            collection_name=self.collection_name,
            embedding_function=self.embeddings,
        )

    async def search(
        self,
        query: str,
        limit: int = 5,
        source_ids: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Выполняет асинхронный семантический поиск с фильтрацией по source_ids."""
        search_filter = (
            {"source_id": {"$in": source_ids}}
            if source_ids
            else None
        )

        # Используем asimilarity_search вместо retriever,
        # чтобы динамически передавать limit и filter в каждый запрос
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
        """Возвращает список уникальных source_id из коллекции ChromaDB."""
        collection = self._client.get_or_create_collection(
            name=self.collection_name
        )
        data = collection.get(include=["metadatas"])
        metadatas = data.get("metadatas") or []

        sources = {
            meta.get("source_id")
            for meta in metadatas
            if meta and "source_id" in meta
        }
        return sorted(list(filter(None, sources)))
