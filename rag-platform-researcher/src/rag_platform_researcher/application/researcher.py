"""Сервис для проведения поиска по базе"""
from rag_platform_contracts.researcher import ResearchRequest, ResearchResponse

from rag_platform_researcher.application.rag import RAGService
from rag_platform_researcher.exceptions import ResearcherBaseError

from rag_platform_observability.observability import get_logger

logger = get_logger(__name__)

class ResearcherService:
    """Верхнеуровневый фасад-сервис для обработки API запросов ресерчера."""

    def __init__(self, rag_service: RAGService):
        """Инициализирует сервис, принимая готовый RAG-движок."""
        self.rag_service = rag_service

    async def execute(self, request: ResearchRequest) -> ResearchResponse:
        """Принимает контракт запроса, запускает RAG-анализ и 
        гарантирует возврат контракта ответа."""
        try:
            # Передаем задачу в изолированный RAG-сервис
            result = await self.rag_service.execute(task=request.task)

            return ResearchResponse(
                workflow_id=request.workflow_id,
                result=result,
                success=True,
            )
        except ResearcherBaseError as e:
            logger.exception("Контролируемый сбой бизнес-логики ресерча")
            return ResearchResponse(
                workflow_id=request.workflow_id,
                result="",
                success=False,
                error=str(e),
            )
