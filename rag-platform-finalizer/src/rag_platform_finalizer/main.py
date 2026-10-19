"""Finalizer entry point"""
from contextlib import asynccontextmanager

import uvicorn
import httpx

from fastapi import FastAPI, HTTPException, Depends

from langchain_core.language_models import BaseChatModel


from rag_platform_finalizer.dependencies import get_llm
from rag_platform_finalizer.presentation.router import router
from rag_platform_finalizer.config.settings import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """lifespan for start/end regularisation"""
    # ==========================================
    # 🚀 ФАЗА STARTUP (Выполняется при старте)
    # ==========================================
    print("🤖 Инициализация RAG Platform Finalizer...")

    # 1. Создаем единый HTTP-клиент для всего приложения
    # Его можно будет переиспользовать в сервисах через app.state.http_client
    app.state.http_client = httpx.AsyncClient(timeout=httpx.Timeout(60.0))

    # 2. Проверяем связь с LLM-провайдером
    try:
        print(f"🔗 Проверка связи с LLM ({settings.provider})...")
        llm = get_llm()
        # Легковесный запрос для проверки коннекта
        await llm.ainvoke("ping")
        print("✅ Связь с LLM успешно установлена!")
    except Exception as e:
        print(f"❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось подключиться к LLM: {e}")
        # Закрываем клиент перед падением
        await app.state.http_client.aclose()
        # Выбрасываем ошибку — uvicorn остановится и контейнер перезапустится
        raise RuntimeError("LLM provider is unreachable") from e

    yield  # В этой точке сервис начинает принимать запросы пользователей

    # ==========================================
    # 🛑 ФАЗА SHUTDOWN (Выполняется при остановке)
    # ==========================================
    print("⏳ Завершение работы RAG Platform Finalizer...")

    # Гарантированно закрываем коннекты, чтобы избежать утечек памяти
    await app.state.http_client.aclose()

    print("🛑 Сервис успешно остановлен.")


app = FastAPI(
    title="RAG Platform Finalizer",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(router, prefix="/api/v1/finalizer")


@app.get("/health")
async def health() -> dict[str, str]:
    """health check"""
    return {"status": "ok"}


@app.get("/ready")
async def ready(llm: BaseChatModel = Depends(get_llm)) -> dict[str, str]:
    """Проверка готовности сервиса и его ключевых зависимостей."""
    try:
        # Проверяем, отвечает ли модель (делаем легковесный проверочный вызов)
        # Для LangChain это метод ainvoke или simple аспект проверки связи
        if hasattr(llm, "client") or hasattr(llm, "base_url"):
            # Точечная проверка для Ollama/OpenAI (опционально, зависит от провайдера)
            # Самый надежный способ — отправить пустой копеечный запрос к API
            await llm.ainvoke("ping")

        return {"status": "ready", "llm_provider": "connected"}
    except Exception as e:
        # Если Ollama недоступна или ключ OpenAI невалиден, отдаем 503 Service Unavailable
        raise HTTPException(
            status_code=503,
            detail=f"Service unavailable: LLM provider connection failed. Error: {str(e)}"
        # Добавляем "from e", чтобы связать исключения и убрать предупреждение Pylint
        ) from e


if __name__ == "__main__":
    # Uvicorn сам возьмет правильный порт из Pydantic Settings
    uvicorn.run("rag_platform_finalizer.main:app", host="0.0.0.0", port=settings.port)
