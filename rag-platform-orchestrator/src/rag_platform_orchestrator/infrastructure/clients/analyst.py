"""Analyst client"""
import time
import httpx

from rag_platform_orchestrator.infrastructure.http import ServiceClient
from rag_platform_orchestrator.config.settings import settings

from rag_platform_contracts.results import (
    AgentExecutionResponse,
)

from rag_platform_contracts.analyst import (
    AnalysisRequest,
    AnalysisResponse,
)


from rag_platform_observability.observability import get_logger


logger = get_logger(__name__)


class AnalystClient(ServiceClient):
    """Class analyst client"""
    async def execute(
        self,
        *,
        user_input: str,
        workflow_id: str,
        task: str,
        research_result: str | None,
    ) -> AgentExecutionResponse:
        """analyst executor"""

        if settings.debug_rag:
            logger.debug(f"[ANALYST CLIENT] POST {self.base_url}/... task={task!r}")
        request = AnalysisRequest(
            user_input=user_input,
            context={
                "workflow_id": workflow_id,
                "task": task,
                "research_result": research_result
            }
        )
        start = time.monotonic()

        try:
            response = await self.client.post(
                f"{self.base_url}/api/v1/analyst/analyze",
                json=request.model_dump(),
            )

        except httpx.ReadTimeout:
            if settings.debug_rag:
                logger.debug(f"[ANALYST CLIENT] ReadTimeout after \
                                {time.monotonic() - start:.1f}s")
            raise
        else:
            response.raise_for_status()

        analyst_data = AnalysisResponse.model_validate(
            response.json()
        )

        return AgentExecutionResponse(
            agent="analyst",
            task=task,
            success=True,
            result=analyst_data.model_dump()
        )
