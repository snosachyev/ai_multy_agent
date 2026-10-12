"""analyst router"""
from fastapi import APIRouter, Depends

# Импортируем существующие инструменты и контракты
from rag_platform_analyst.application.analyst import AnalystService

from rag_platform_analyst.dependencies import get_analyst_service

from rag_platform_contracts.analyst import AnalysisRequest, AnalysisResponse

router = APIRouter()


@router.post(
    "/analyze",
    response_model=AnalysisResponse,
)
async def analyze(
    request: AnalysisRequest,
    service: AnalystService = Depends(get_analyst_service),
) -> AnalysisResponse:
    """Эндпоинт для запуска процесса анализа."""
    return await service.execute(request)
