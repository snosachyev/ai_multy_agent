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
    SourcesResponse,
)


from rag_platform_observability.observability import get_logger


logger = get_logger(__name__)


class ResearcherClient(ServiceClient):
    """Инфраструктурный клиент исследователя (Stateless)."""

    async def get_sources(self) -> list[str]:
        """Запрашивает у Researcher список доступных источников знаний."""
        response = await self.client.get(
            f"{self.base_url}/api/v1/researcher/sources",
        )
        response.raise_for_status()
        sources_data = SourcesResponse.model_validate(response.json())
        return sources_data.sources


    async def execute(
        self,
        *,
        user_input: str,
        workflow_id: str,
        task: str | None,
        source_ids: list[str] | None = None,
    ) -> AgentExecutionResponse:
        """Интеграционный метод выполнения подзадачи агента."""
        # Инкапсулируем логику выбора контекста внутри интеграционного слоя
        final_task = task or user_input

        request = ResearchRequest(
            task=final_task,
            workflow_id=workflow_id,
            source_ids=source_ids
        )
        start = time.monotonic()

        if settings.debug_rag:
            logger.debug(
                "[RESEARCHER CLIENT] POST %s/api/v1/researcher/search task=%r, source_ids=%s",
                self.base_url,
                final_task,
                source_ids,
            )

        try:
            response = await self.client.post(
                f"{self.base_url}/api/v1/researcher/search",
                json=request.model_dump(),
                # При необходимости для тяжелых LLM-запросов переопределяем таймаут "на лету":
                # timeout=httpx.Timeout(120.0)
            )
        except httpx.ReadTimeout:
            if settings.debug_rag:
                logger.debug(
                    "[RESEARCHER CLIENT] ReadTimeout after %.1fs",
                    time.monotonic() - start,
                )
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
