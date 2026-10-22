"""Orchestration entrypoint"""
from contextlib import asynccontextmanager
import asyncio
import httpx

from fastapi import FastAPI, HTTPException, status

from rag_platform_orchestrator.config.settings import settings
from rag_platform_orchestrator.presentation.router import router

from rag_platform_orchestrator.presentation.dependencies import (
    get_workflow,
)


@asynccontextmanager
async def lifespan(fastapi_app: FastAPI):
    """lifespan for start/end regularisation"""
    print("🤖 Инициализация RAG Platform Analyst...")

    # Открываем единственный глобальный пул соединений
    async with httpx.AsyncClient(
        timeout=httpx.Timeout(connect=5.0, read=60.0, write=10.0, pool=10.0)
    ) as http_client:

        # Сохраняем в app.state для ручек /ready или сторонних нужд (опционально)
        fastapi_app.state.http_client = http_client

        # Инициализируем и жестко кэшируем синглтон-граф Workflow
        fastapi_app.state.workflow = get_workflow(http_client)

        yield  # Приложение принимает входящий трафик

    print("🛑 Сервис успешно остановлен, все соединения закрыты автоматически.")


app = FastAPI(
    title="RAG Platform Orchestrator",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(router, prefix="/api/v1/workflows")


@app.get("/health")
async def health() -> dict[str, str]:
    """health check"""
    return {"status": "ok"}


@app.get("/ready")
async def ready() -> dict[str, str]:
    """ready check with agent pings"""
    # Базовая проверка инициализации
    if not hasattr(app.state, "workflow") or not hasattr(app.state, "http_client"):
        raise HTTPException(status_code=503, detail="App not initialized")

    client: httpx.AsyncClient = app.state.http_client

    # Список базовых URL ваших сервисов-агентов (можно забрать из settings)
    services_to_check = [
        f"{settings.director_service_url}/health",
        f"{settings.analyst_service_url}/health",
        f"{settings.researcher_service_url}/health",
        f"{settings.finalizer_service_url}/health",
    ]

    # Функция для быстрого пинга одного сервиса
    async def ping(url: str) -> bool:
        try:
            # Используем встроенный в client таймаут или переопределяем его здесь
            response = await client.get(url, timeout=1.5)
            return response.status_code == 200
        except httpx.RequestError:
            # Перехватит: httpx.ConnectTimeout, httpx.ReadTimeout, httpx.ConnectError и т.д.
            # Но НЕ скроет ошибки в коде (например, если вы опечатаетесь в имени переменной)
            return False

    # Запускаем все пинги ОДНОВРЕМЕННО, чтобы не копить таймауты последовательно
    results = await asyncio.gather(*(ping(url) for url in services_to_check))

    # Если хотя бы один критический сервис недоступен — оркестратор НЕ готов
    if not all(results):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="One or more downstream services (agents) are unavailable"
        )

    return {"status": "ready"}
