"""Researcher entry point"""

from contextlib import asynccontextmanager
import httpx
import uvicorn
from fastapi import Depends, FastAPI, HTTPException
from prometheus_client import make_asgi_app

from langchain_core.language_models import BaseChatModel
from rag_platform_researcher.config.settings import settings
from rag_platform_researcher.dependencies import (
    get_llm,
    init_vector_store
)
from rag_platform_researcher.presentation.router import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan для инициализации инфраструктуры и контроля ресурсов."""
    # ==========================================
    # 🚀 ФАЗА STARTUP (Выполняется при старте)
    # ==========================================
    print("🤖 Инициализация RAG Platform Researcher...")

    # 1. Создаем единый HTTP-клиент для всего приложения
    app.state.http_client = httpx.AsyncClient(timeout=httpx.Timeout(60.0))

    # 2. Инициализируем и прогреваем Chroma Vector Store в памяти один раз
    try:
        print("⏳ Загрузка эмбеддингов и развертывание Chroma в памяти...")
        init_vector_store(app)
        print("✅ Векторная база Chroma успешно инициализирована!")
    except Exception as e:
        print(f"❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось поднять Chroma: {e}")
        await app.state.http_client.aclose()
        raise RuntimeError("Vector store initialization failed") from e

    # 3. Проверяем связь с LLM-провайдером
    try:
        print(f"🔗 Проверка связи с LLM ({settings.provider})...")
        llm = get_llm()
        await llm.ainvoke("ping")
        print("✅ Связь с LLM успешно установлена!")
    except Exception as e:
        print(f"❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось подключиться к LLM: {e}")
        await app.state.http_client.aclose()
        raise RuntimeError("LLM provider is unreachable") from e

    yield  # В этой точке сервис начинает принимать запросы пользователей

    # ==========================================
    # 🛑 ФАЗА SHUTDOWN (Выполняется при остановке)
    # ==========================================
    print("⏳ Завершение работы RAG Platform Researcher...")

    # Гарантированно закрываем коннекты, чтобы избежать утечек памяти
    await app.state.http_client.aclose()

    print("🛑 Сервис успешно остановлен.")


app = FastAPI(
    title="RAG Platform Researcher",
    version="1.0.0",
    lifespan=lifespan,
)

# ============================================================
# PROMETHEUS METRICS
# ============================================================
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# ============================================================
# ROUTERS
# ============================================================
# Стандартное подключение чистого объекта роутера, как во всех сервисах
app.include_router(router, prefix="/api/v1/researcher")


@app.get("/health")
async def health() -> dict[str, str]:
    """Простая проверка жизнеспособности процесса."""
    return {"status": "ok"}


@app.get("/ready")
async def ready(llm: BaseChatModel = Depends(get_llm)) -> dict[str, str]:
    """Проверка готовности сервиса и его ключевых зависимостей (Readiness Probe)."""
    try:
        if hasattr(llm, "client") or hasattr(llm, "base_url"):
            await llm.ainvoke("ping")

        return {"status": "ready", "llm_provider": "connected"}
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Service unavailable: LLM provider connection failed. Error: {str(e)}",
        ) from e


if __name__ == "__main__":
    # Uvicorn автоматически подхватит порт из Pydantic Settings
    uvicorn.run(
        "rag_platform_researcher.main:app", host="0.0.0.0", port=settings.port
    )
