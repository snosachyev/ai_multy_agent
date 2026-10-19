
"""Finalizer RAG service"""
from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from rag_platform_contracts.finalizer import FinalizationRequest, FinalizationResponse


class FinalizerService:
    """Сервис для проведения финального вывода с помощью LLM."""
    def __init__(self, llm: BaseChatModel) -> None:
        """Инициализирует сервис подведения итогов с заданной языковой моделью.

        Args:
            llm: Экземпляр чат-модели LangChain, поддерживающий структурированный вывод.
        """
        self.llm = llm
        self.chain = self._build_prompt() | self.llm.with_structured_output(
            FinalizationResponse
        )


    @staticmethod
    def _build_prompt():

        return ChatPromptTemplate.from_messages([
            (
                "system",
                """
                Ты — Главный Директор.

                Сформируй финальный ответ пользователю.

                Используй результаты Researcher и Analyst.

                Ответ должен быть:

                - точным;
                - структурированным;
                - понятным;
                - на русском языке.

                Не упоминай внутреннюю архитектуру
                агентов, если это не требуется вопросом.
                """,
            ),
            (
                "human",
                """
                Задача пользователя:

                {user_input}

                Researcher:

                {research_result}

                Analyst:

                {analysis_result}

                Сформируй финальный ответ.
                """,
            ),
        ])

    async def execute( # TO DO mix with finalize
        self,
        user_input: str,
        research_result: str | None,
        analysis_result: str | None,
    ) -> str:

        return await self.chain.ainvoke({
            "user_input": user_input,
            "research_result":
                research_result or "Нет данных.",
            "analysis_result":
                analysis_result or "Нет данных.",
        })


    async def finalize(
            self,
            request: FinalizationRequest,
        ) -> FinalizationResponse:

            # Временная реализация.
            # Здесь позже будет LLM для формирования
            # финального ответа.

            parts = []
    
            if request.researcher_result:
                parts.append(request.researcher_result)
    
            if request.analysis_result:
                parts.append(request.analysis_result)
    
            final_answer = "\n\n".join(parts)
            return FinalizationResponse(
                workflow_id=request.workflow_id,
                final_answer=final_answer,
                success=True,
            )
