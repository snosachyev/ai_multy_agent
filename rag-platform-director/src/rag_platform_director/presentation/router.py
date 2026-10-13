"""director router"""
from fastapi import APIRouter, Depends

# Импортируем существующие инструменты и контракты
from rag_platform_director.application.director import DirectorService

from rag_platform_director.dependencies import get_director_service

from rag_platform_contracts.director import DirectorDecision, DirectorRequest

router = APIRouter()


@router.post(
    "/decide",
    response_model=DirectorDecision,
)
async def decide(
    request: DirectorRequest,
    service: DirectorService = Depends(get_director_service),
) -> DirectorDecision:
    """Эндпоинт для запуска процесса выбора агента."""
    return await service.decide(request)
