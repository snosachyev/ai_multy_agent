"""Поисковик хранилища"""
import pickle

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

from rag_platform_researcher.application.rag import VectorStorePort


class ChromaVectorStore(
    VectorStorePort,
):
    """Класс поисковик векторного хранилища"""
    def __init__(
        self,
        splits_path: str,
    ):
        with open(splits_path, "rb") as f:
            splits = pickle.load(f)

        embeddings = HuggingFaceEmbeddings(
            model_name="intfloat/multilingual-e5-base",
            model_kwargs={
                "device": "cpu",
            },
        )

        self.vectorstore = Chroma.from_documents(
            documents=splits,
            embedding=embeddings,
        )

        self.retriever = (
            self.vectorstore.as_retriever(
                search_kwargs={
                    "k": 5,
                }
            )
        )

    async def search(
        self,
        query: str,
        limit: int = 5,
    ) -> list[dict]:

        # LangChain retriever,
        # вызываем его через async API

        documents = await self.retriever.ainvoke(
            query
        )

        documents = documents[:limit]

        return [
            {
                "id": document.metadata["document_id"],
                "content": document.page_content,
                "metadata": document.metadata,
            }
            for document in documents
        ]
