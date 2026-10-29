"""Мок сервер что бы не ждать слабую локальную LLM или не протестить без использования токенов"""
import asyncio
import uvicorn

from fastapi import FastAPI

# --- Эндпоинты ---
# Импортируем оригинальные контракты и DTO, как в продакшен-коде!
from rag_platform_contracts.director import (
    DirectorDecision,
    DirectorRequest
)

from rag_platform_contracts.researcher import (
    ResearchRequest,
    ResearchResponse,
    RAGResult,
    RetrievedDocument
)

from rag_platform_contracts.analyst import (
    AnalysisRequest,
    AnalysisResponse,
)

from rag_platform_contracts.finalizer import (
    FinalizationRequest,
    FinalizationResponse,
)



app = FastAPI(title="RAG Platform - Smart Infrastructure Mock")


# =====================================================================
# 1. ДИРЕКТОР (POST /api/v1/director/decide)
# =====================================================================
@app.post("/api/v1/director/decide", response_model=DirectorDecision)
async def mock_director_decide(request: DirectorRequest):
    """Эметируем раьобту director сервера"""
    await asyncio.sleep(0.04)  # Имитируем сетевую задержку 40мс

    context = request.context
    iteration = context.get("iteration", 0)

    # Эмуляция пошагового выполнения воркфлоу с учетом реального контракта
    if iteration == 0:
        return DirectorDecision(
            next_action="researcher",
            reason="Необходимо собрать начальный контекст по RAG.",
            task="Собрать базовую информацию по запросу RAG."
        )
    elif iteration == 1:
        return DirectorDecision(
            next_action="analyst",
            reason="Контекст собран, переходим к этапу валидации данных.",
            task="Провести глубокий анализ собранных данных."
        )

    # На 2+ итерации завершаем граф
    return DirectorDecision(
        next_action="finish",
        reason="Все агенты успешно отработали, лимит итераций не превышен.",
        task="Анализ завершен, формируем финальный ответ."
    )

# =====================================================================
# 2. ИССЛЕДОВАТЕЛЬ (POST /api/v1/researcher/search)
# =====================================================================
@app.post("/api/v1/researcher/search", response_model=ResearchResponse)
async def mock_researcher_search(request: ResearchRequest):
    """Эметируем раьобту researcher сервера"""
    await asyncio.sleep(0.06)  # Имитируем работу эмбеддингов/векторной БД (60мс)

    # Строим строгий ответ, который ожидает нода `result.result['result']['answer']`
    fake_rag_result = RAGResult(
        question=request.task,
        generated_queries=["what is rag", "rag definition"],
        documents=[
            RetrievedDocument(
                id="doc_1",
                content="RAG stands for Retrieval-Augmented Generation.",
                metadata={"source": "mock_db"}
            )
        ],
        context="Retrieval-Augmented Generation (RAG) is a technique that" \
        "grants LLMs access to external data.",
        answer="RAG (Retrieval-Augmented Generation) — это подход, совмещающий" \
        "поиск документов и генерацию текста."
    )

    return ResearchResponse(
        workflow_id=request.workflow_id,
        result=fake_rag_result,
        success=True,
        error=None
    )

# =====================================================================
# 3. АНАЛИТИК (POST /api/v1/analyst/analyze)
# =====================================================================
@app.post("/api/v1/analyst/analyze")
async def mock_analyst_analyze(request: AnalysisRequest):
    """Эметируем раьобту analyst сервера"""
    await asyncio.sleep(0.05)  # Имитируем размышления аналитика (50мс)

    # Извлекаем workflow_id из контекста запроса, чтобы вернуть его назад
    context = request.context
    workflow_id = context.get("workflow_id", "mock-workflow-id")

    # Возвращаем строгую структуру для AnalysisResponse:
    # Поле result должно быть плоской СТРОКОЙ, а не словарем!
    return AnalysisResponse(
        workflow_id=workflow_id,
        result="Анализ подтверждает: предоставленный " \
        "RAG-контекст полностью решает задачу пользователя.",
        success=True,
        error=None
    )


# =====================================================================
# 4. ФИНАЛИЗАТОР (POST /api/v1/finalizer/finalizer)
# =====================================================================
@app.post("/api/v1/finalizer/finalizer", response_model=FinalizationResponse)
async def mock_finalizer_finalize(request: FinalizationRequest):
    """Используем оригинальный FinalizationResponse для строгого соответствия контракту на выходе"""
    await asyncio.sleep(0.04)  # Имитируем сборку финального ответа (40мс)

    # Формируем структуру, которую клиент прочитает через data["success"] и data["final_answer"]
    return FinalizationResponse(
        workflow_id=request.workflow_id,
        final_answer="Финальный ответ: RAG — это паттерн проектирования " \
        "ИИ-систем, оптимизирующий ответы LLM.",
        success=True,
        error=None
    )

@app.get("/health")
async def health() -> dict[str, str]:
    """Простая проверка жизнеспособности процесса."""
    return {"status": "ok"}

if __name__ == "__main__":
    print('9000')
    uvicorn.run(app, host="0.0.0.0", port=9000)
