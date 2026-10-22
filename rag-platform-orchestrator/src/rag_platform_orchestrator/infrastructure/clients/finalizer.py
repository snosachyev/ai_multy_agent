"""Finalizer client"""
import time
import httpx

from rag_platform_orchestrator.infrastructure.http import (
    ServiceClient,
)

from rag_platform_orchestrator.config.settings import settings

from rag_platform_contracts.finalizer import (
    FinalizationRequest,
    FinalizationResponse,
)

from rag_platform_observability.observability import get_logger


logger = get_logger(__name__)


class FinalizerClient(ServiceClient):
    """Class finalizer client"""
    async def execute(
        self,
        *,
        workflow_id: str,
        user_input: str,
        research_result: str | None,
        analysis_result: str | None,
    ) -> str:
        """finalizer executor"""
        request = FinalizationRequest(
            workflow_id=workflow_id,
            user_input=user_input,
            researcher_result=research_result,
            analysis_result=analysis_result,
        )

        start = time.monotonic()

        if settings.debug_rag:
            logger.debug(f"[FINALIZER CLIENT] POST {self.base_url}/... user_input={user_input!r}")

        try:
            response = await self.client.post(
                f"{self.base_url}/api/v1/finalizer/finalizer",
                json=request.model_dump(),
            )
        except httpx.ReadTimeout:
            if settings.debug_rag:
                logger.debug(f"[FINALIZER CLIENT] ReadTimeout after \
                                {time.monotonic() - start:.1f}s")
            raise

        else:
            response.raise_for_status()

        finalization_data = FinalizationResponse.model_validate(
            response.json()
        )

        if not finalization_data.success:
            raise RuntimeError(
                finalization_data.error
                or "Finalizer failed"
            )

        return finalization_data.final_answer
