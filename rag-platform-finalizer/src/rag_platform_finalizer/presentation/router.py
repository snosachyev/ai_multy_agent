"""finalizer router"""
from fastapi import APIRouter, Depends

# Импортируем существующие инструменты и контракты
from rag_platform_finalizer.application.finalizer import FinalizerService

from rag_platform_finalizer.dependencies import get_finalizer_service

from rag_platform_contracts.finalizer import FinalizationRequest, FinalizationResponse

router = APIRouter()


@router.post(
    "/finalizer",
    response_model=FinalizerService,
)
async def finalize(
    request: FinalizationRequest,
    service: FinalizerService = Depends(get_finalizer_service),
) -> FinalizationResponse:
    """Эндпоинт для запуска процесса анализа."""
    return await service.execute(request)
