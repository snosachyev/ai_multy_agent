FROM ghcr.io/snosachyev/rag-python-base:latest AS orchestrator-base

WORKDIR /app

# 1. Копируем собранные wheel-пакеты во временную папку
COPY packages/ /tmp/packages/

# 2. Копируем pyproject.toml и исходный код аналитика в рабочую директорию /app
COPY rag-platform-orchestrator/pyproject.toml .
COPY rag-platform-orchestrator/src ./src

# 3. Сначала ставим контракт из wheel, а затем аналитик в режиме редактирования (-e .)
# Мы используем "." потому что pyproject.toml лежит прямо в /app
RUN pip install --no-cache-dir /tmp/packages/rag_platform_contracts-1.0.0-py3-none-any.whl \
    /tmp/packages/rag_platform_observability-1.0.0-py3-none-any.whl

RUN pip install --no-cache-dir .

# =========================================
# Runtime
# =========================================

FROM orchestrator-base AS runtime

RUN pip install --no-cache-dir \
    /tmp/packages/rag_platform_llm-1.0.0-py3-none-any.whl

ENV PYTHONPATH=/app/src
# 4. Запускаем uvicorn, указывая следить за изменениями в рабочей директории /app/src
CMD ["sh", "-c", "uvicorn rag_platform_orchestrator.main:app --host 0.0.0.0 --port $PORT --reload --reload-dir /app"]


# =========================================
# Evaluation
# =========================================

FROM orchestrator-base AS evaluation

RUN pip install --no-cache-dir "psycopg[binary]"

COPY evaluation/orchestrator ./evaluation/orchestrator
COPY evaluation/common ./evaluation/common

ENV PYTHONPATH=/app/src

CMD ["python", "-m", "evaluation.orchestrator.run_evaluation", "--mode", "smoke"]
