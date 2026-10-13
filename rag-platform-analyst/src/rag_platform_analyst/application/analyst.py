"""Сервис для проведения аналити результов"""
from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from rag_platform_contracts.analyst import AnalysisRequest, AnalysisResponse


class AnalystService:
    """Сервис для проведения аналитических расчетов и логического анализа с помощью LLM."""

    def __init__(self, llm: BaseChatModel) -> None:
        """Инициализирует сервис аналитики с заданной языковой моделью.

        Args:
            llm: Экземпляр чат-модели LangChain, поддерживающий структурированный вывод.
        """
        self.llm = llm
        self.chain = self._build_prompt() | self.llm.with_structured_output(
            AnalysisResponse
        )

    @staticmethod
    def _build_prompt() -> ChatPromptTemplate:
        """Создает и возвращает шаблон промпта для системного и пользовательского ввода.

        Returns:
            ChatPromptTemplate: Скомпилированный шаблон сообщений для LangChain.
        """
        return ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """
                Ты — профессиональный аналитик.

                Твоя задача:
                - выполнять математические расчеты;
                - анализировать код;
                - решать логические задачи;
                - использовать результаты Researcher.

                Отвечай точно.
                Проверяй расчеты.
                """,
                ),
                (
                    "human",
                    """
                Исходная задача:
                {user_input}

                Конкретная задача:
                {task}

                Информация Researcher:
                {research_result}

                Выполни анализ.
                """,
                ),
            ]
        )

    async def execute(self, request: AnalysisRequest) -> AnalysisResponse:
        """Запускает цепочку анализа на основе входящего запроса.

        Args:
            request: Объект контракта AnalysisRequest с входными данными и контекстом.

        Returns:
            AnalysisResponse: Валидированный структурированный ответ от LLM.
        """
        context = request.context

        chain_result: AnalysisResponse = await self.chain.ainvoke(
            {
                "user_input": request.user_input,
                "workflow_id": context.get("workflow_id"),
                "task": context.get("task"),
                "research_result": context.get("research_result")
                or "Нет данных.",
            }
        )

        return chain_result
