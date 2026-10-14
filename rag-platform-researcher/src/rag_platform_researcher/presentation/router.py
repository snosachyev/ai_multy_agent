"""researcher router"""
from fastapi import APIRouter, Depends
from rag_platform_contracts.researcher import ResearchRequest, ResearchResponse
from rag_platform_researcher.application.researcher import ResearcherService
from rag_platform_researcher.dependencies import get_researcher_service

router = APIRouter()

@router.post(
    "/search",
    response_model=ResearchResponse,
)
async def search(
    request: ResearchRequest,
    service: ResearcherService = Depends(get_researcher_service),
) -> ResearchResponse:
    """Эндпоинт для запуска процесса поиска по RAG-платформе."""
    # Метод теперь называется execute, один в один как у аналитика!
    return await service.execute(request)
