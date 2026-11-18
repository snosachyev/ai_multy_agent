"""ETL-воркер для валидации и загрузки чанков в векторные хранилища (Qdrant / Chroma)."""

import argparse
import json
import os
import pickle
import uuid
from pathlib import Path
from typing import Literal

import chromadb
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams

from rag_platform_contracts.vector_store import (
    EMBEDDING_MODEL_NAME,
    EMBEDDING_VECTOR_SIZE,
    QDRANT_COLLECTION_NAME,
    DocumentChunkMetadata,
)


def _load_and_validate_docs(file_path: str, source_id: str) -> list[Document]:
    """Читает чанки из файла и валидирует их метаданные по общему контракту."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Файл не найден: {path}")

    if path.suffix == ".json":
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        raw_docs = [
            Document(page_content=d["page_content"], metadata=d["metadata"])
            for d in raw
        ]
    else:
        with open(path, "rb") as f:
            raw_docs = pickle.load(f)

    validated_docs: list[Document] = []
    for doc in raw_docs:
        meta_dict = {**doc.metadata, "source_id": source_id}
        validated_meta = DocumentChunkMetadata(**meta_dict)
        validated_docs.append(
            Document(
                page_content=doc.page_content,
                metadata=validated_meta.model_dump(exclude_none=True),
            )
        )

    return validated_docs


def run_ingestion(
    file_path: str,
    source_id: str,
    backend: Literal["qdrant", "chroma"] = "qdrant",
    qdrant_url: str = "http://qdrant:6333",
    chroma_host: str = "chroma",
    chroma_port: int = 8000,
) -> None:
    """Валидирует метаданные по контракту и загружает чанки в выбранную векторную БД.

    Args:
        file_path: Путь к файлу с чанками (.json или .pkl).
        source_id: Уникальный идентификатор источника для фильтрации.
        backend: Целевое хранилище ("qdrant" или "chroma").
        qdrant_url: URL-адрес сервера Qdrant.
        chroma_host: Хост сервера ChromaDB.
        chroma_port: Порт сервера ChromaDB.
    """
    validated_docs = _load_and_validate_docs(file_path=file_path, source_id=source_id)

    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL_NAME,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )

    ids = [
        str(uuid.uuid5(uuid.NAMESPACE_DNS, doc.metadata["document_id"]))
        for doc in validated_docs
    ]

    if backend == "qdrant":
        client = QdrantClient(url=qdrant_url)
        if not client.collection_exists(QDRANT_COLLECTION_NAME):
            client.create_collection(
                collection_name=QDRANT_COLLECTION_NAME,
                vectors_config=VectorParams(
                    size=EMBEDDING_VECTOR_SIZE,
                    distance=Distance.COSINE,
                ),
            )

        vector_store = QdrantVectorStore(
            client=client,
            collection_name=QDRANT_COLLECTION_NAME,
            embedding=embeddings,
        )
        vector_store.add_documents(documents=validated_docs, ids=ids)

    elif backend == "chroma":
        client = chromadb.HttpClient(host=chroma_host, port=chroma_port)
        print('client', client)
        vector_store = Chroma(
            client=client,
            collection_name=QDRANT_COLLECTION_NAME,
            embedding_function=embeddings,
        )
        print('vector_store', vector_store)
        vector_store.add_documents(documents=validated_docs, ids=ids)
        print('done')

    else:
        raise ValueError(f"Неподдерживаемый бэкенд векторного хранилища: {backend}")

    print(
        f"[Ingestion:{backend}] Загружено {len(validated_docs)} чанков "
        f"для source_id='{source_id}' в коллекцию '{QDRANT_COLLECTION_NAME}'."
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ETL-загрузчик чанков в векторную БД")
    parser.add_argument("--file", required=True, help="Путь к файлу внутри контейнера")
    parser.add_argument("--source-id", required=True, help="Идентификатор источника")
    parser.add_argument(
        "--backend",
        choices=["qdrant", "chroma"],
        default=os.getenv("VECTOR_STORE_TYPE", "qdrant"),
        help="Целевая векторная база (qdrant или chroma)",
    )
    parser.add_argument(
        "--qdrant-url",
        default=os.getenv("QDRANT_URL", "http://qdrant:6333"),
        help="URL сервера Qdrant",
    )
    parser.add_argument(
        "--chroma-host",
        default=os.getenv("CHROMA_HOST", "chroma"),
        help="Хост сервера ChromaDB",
    )
    parser.add_argument(
        "--chroma-port",
        type=int,
        default=int(os.getenv("CHROMA_PORT", "8000")),
        help="Порт сервера ChromaDB",
    )

    args = parser.parse_args()
    run_ingestion(
        file_path=args.file,
        source_id=args.source_id,
        backend=args.backend,
        qdrant_url=args.qdrant_url,
        chroma_host=args.chroma_host,
        chroma_port=args.chroma_port,
    )
