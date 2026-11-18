"""Общие константы и Pydantic-схемы метаданных для ETL-пайплайна и Researcher."""

from pydantic import BaseModel, Field

# Единые константы для ETL и Researcher
QDRANT_COLLECTION_NAME = "rag_documents"
EMBEDDING_MODEL_NAME = "intfloat/multilingual-e5-base"
EMBEDDING_VECTOR_SIZE = 768


class DocumentChunkMetadata(BaseModel):
    """Контракт метаданных чанка, записываемых в Qdrant."""
    document_id: str = Field(
        ..., description="Уникальный ID чанка (например, lilian-weng-agent-0001)"
    )
    source_id: str = Field(..., description="Идентификатор источника для фильтрации (select)")
    source: str | None = Field(default=None, description="URL или имя исходного файла")
    start_index: int | None = Field(default=None, description="Позиция чанка в исходном тексте")


class QdrantChunkPayload(BaseModel):
    """Схема хранения точки в Qdrant (совместимая с LangChain QdrantVectorStore)."""
    page_content: str
    metadata: DocumentChunkMetadata
