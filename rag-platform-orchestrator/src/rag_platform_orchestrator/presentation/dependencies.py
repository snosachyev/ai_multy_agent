"""Модуль создания workflow для графа"""
from functools import lru_cache
import httpx

from fastapi import Request

from rag_platform_orchestrator.application.workflow import (
    Workflow,
)

from rag_platform_orchestrator.config.settings import settings

from rag_platform_orchestrator.infrastructure.clients.director import (
    DirectorClient,
)

from rag_platform_orchestrator.infrastructure.clients.researcher import (
    ResearcherClient,
)

from rag_platform_orchestrator.infrastructure.clients.analyst import (
    AnalystClient,
)

from rag_platform_orchestrator.infrastructure.clients.finalizer import (
    FinalizerClient,
)


def get_workflow_graph(request: Request) -> Workflow:
    """Извлекает готовый граф из состояния приложения (вызывается через Depends)."""
    return request.app.state.workflow


@lru_cache(maxsize=1)
def get_workflow(http_client: httpx.AsyncClient) -> Workflow:
    """Собирает и кэширует граф Workflow ровно один раз на всю жизнь процесса."""
    return Workflow(
        director=DirectorClient(client=http_client, base_url=settings.director_service_url),
        researcher=ResearcherClient(client=http_client, base_url=settings.researcher_service_url),
        analyst=AnalystClient(client=http_client, base_url=settings.analyst_service_url),
        finalizer=FinalizerClient(client=http_client, base_url=settings.finalizer_service_url),
    )
