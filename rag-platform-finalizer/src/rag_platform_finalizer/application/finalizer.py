"""Finalizer RAG service"""

from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from rag_platform_contracts.finalizer import FinalizationRequest, FinalizationResponse
from rag_platform_observability.observability import get_logger

logger = get_logger(__name__)


class FinalizerService:
    """Сервис для формирования финального структурированного вывода с помощью LLM."""

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
    def _build_prompt() -> ChatPromptTemplate:
        """Создает и возвращает шаблон промпта для финального синтеза ответов.

        Returns:
            ChatPromptTemplate: Скомпилированный шаблон сообщений для LangChain.
        """
        return ChatPromptTemplate.from_messages(
            [
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

                Не упоминай внутреннюю архитектуру агентов, если это не требуется вопросом.
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
            ]
        )

    async def execute(self, request: FinalizationRequest) -> FinalizationResponse:
        """Запускает цепочку генерации финального ответа на основе собранного контекста.

        Args:
            request: Объект контракта FinalizationRequest с результатами работы агентов.

        Returns:
            FinalizationResponse: Валидированный структурированный ответ для пользователя.
        """
        try:
            # chain_result ЗДЕСЬ — это уже готовый экземпляр FinalizationResponse,
            # так как мы использовали .with_structured_output()
            chain_result: FinalizationResponse = await self.chain.ainvoke(
                {
                    "user_input": request.user_input,
                    "research_result": request.researcher_result or "Нет данных.",
                    "analysis_result": request.analysis_result or "Нет данных.",
                }
            )

            # Принудительно проставляем workflow_id из запроса, если модель его не заполнила
            if hasattr(chain_result, "workflow_id") and not chain_result.workflow_id:
                chain_result.workflow_id = request.workflow_id

            return chain_result

        except Exception as e:  # pylint: disable=broad-exception-caught
            # Наружу ошибку не выбрасываем, а логируем её с полным traceback
            logger.exception("Критический сбой при формировании финального ответа")

            # Гарантируем возврат строгого контракта ответа даже при падении LLM
            return FinalizationResponse(
                workflow_id=request.workflow_id,
                final_answer="Извините, не удалось сформировать " \
                "финальный ответ из-за внутренней ошибки.",
                success=False,
                error=f"Internal finalizer error: {type(e).__name__} - {str(e)}",
            )
