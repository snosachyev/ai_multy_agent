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

    async def get_available_sources(self) -> list[str]:
        """Возвращает список доступных source_id из векторного хранилища."""
        return await self.rag_service.get_available_sources()

    async def execute(self, request: ResearchRequest) -> ResearchResponse:
        """Принимает контракт запроса, запускает RAG-анализ и 
        гарантирует возврат контракта ответа."""
        try:
            # Передаем задачу в изолированный RAG-сервис
            result = await self.rag_service.execute(
                task=request.task,
                source_ids=request.source_ids
            )

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
