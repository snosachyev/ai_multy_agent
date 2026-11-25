"""researcher router"""
from fastapi import APIRouter, Depends
from rag_platform_contracts.researcher import ResearchRequest, ResearchResponse, SourcesResponse
from rag_platform_researcher.application.researcher import ResearcherService
from rag_platform_researcher.dependencies import get_researcher_service

router = APIRouter()


@router.get(
    "/sources",
    response_model=SourcesResponse,
)
async def get_sources(
    service: ResearcherService = Depends(get_researcher_service),
) -> SourcesResponse:
    """Возвращает список доступных источников знаний для фильтрации."""
    sources = await service.get_available_sources()
    return SourcesResponse(sources=sources)


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
