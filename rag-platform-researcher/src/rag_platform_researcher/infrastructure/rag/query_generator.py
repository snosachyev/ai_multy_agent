"""Генератор текста"""
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from rag_platform_researcher.application.rag import QueryGeneratorPort


class LLMQueryGenerator(
    QueryGeneratorPort,
):
    """Класс генератор текста полученного из хранилища 
    и LLM на основе текста генерирует конечный результат"""
    def __init__(self, llm):
        self.llm = llm

        prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                """
                Ты генерируешь поисковые запросы
                для RAG-системы.


                Для данного вопроса создай несколько
                разных поисковых запросов, которые помогут
                найти релевантную информацию в документах.

                Создавай на том же языке, на котором задан вопрос.

                Каждый запрос должен находиться
                на отдельной строке.

                Создай максимум 4 запроса.

                Не добавляй нумерацию.
                """,
            ),
            (
                "human",
                "{question}",
            ),
        ])

        self.chain = (
            prompt
            | self.llm
            | StrOutputParser()
        )

    async def generate(
        self,
        question: str,
    ) -> list[str]:
        raw_queries = await self.chain.ainvoke({
            "question": question,
        })

        return [
            query.strip()
            for query in raw_queries.splitlines()
            if query.strip()
        ]
