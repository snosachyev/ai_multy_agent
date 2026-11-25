"""Фабрика для инициализации модели эмбеддингов."""
from langchain_core.embeddings import Embeddings
from langchain_huggingface import HuggingFaceEmbeddings
from rag_platform_contracts.vector_store import EMBEDDING_MODEL_NAME


def get_embeddings(device: str = "cpu") -> Embeddings:
    """Создает и возвращает настроенный экземпляр HuggingFaceEmbeddings."""
    return HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL_NAME,
        model_kwargs={"device": device},
        encode_kwargs={"normalize_embeddings": True},
    )
