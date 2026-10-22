"""Researcher client"""
import time
import httpx

from rag_platform_orchestrator.infrastructure.http import (
    ServiceClient,
)
from rag_platform_orchestrator.config.settings import settings

from rag_platform_contracts.results import (
    AgentExecutionResponse,
)

from rag_platform_contracts.researcher import (
    ResearchRequest,
    ResearchResponse,
)


from rag_platform_observability.observability import get_logger


logger = get_logger(__name__)


class ResearcherClient(ServiceClient):
    """Инфраструктурный клиент исследователя (Stateless)."""

    async def execute(
        self,
        *,
        user_input: str,
        workflow_id: str,
        task: str | None,
    ) -> AgentExecutionResponse:
        """Интеграционный метод выполнения подзадачи агента."""
        # Инкапсулируем логику выбора контекста внутри интеграционного слоя
        final_task = task or user_input

        request = ResearchRequest(task=final_task, workflow_id=workflow_id)
        start = time.monotonic()

        if settings.debug_rag:
            logger.debug(f"[RESEARCHER CLIENT] POST {self.base_url}/... task={final_task!r}")

        try:
            response = await self.client.post(
                f"{self.base_url}/api/v1/researcher/search",
                json=request.model_dump(),
                # При необходимости для тяжелых LLM-запросов переопределяем таймаут "на лету":
                # timeout=httpx.Timeout(120.0) 
            )
        except httpx.ReadTimeout:
            if settings.debug_rag:
                logger.debug(f"[RESEARCHER CLIENT] ReadTimeout after \
                             {time.monotonic() - start:.1f}s")
            raise
        else:
            response.raise_for_status()

        research_data = ResearchResponse.model_validate(response.json())

        return AgentExecutionResponse(
            agent="researcher",
            task=final_task,  # Возвращаем фактический топик наружу для истории стейта
            success=True,
            result=research_data.model_dump()
        )
