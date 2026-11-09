FROM ghcr.io/snosachyev/rag-python-base:latest AS researcher-base

WORKDIR /app

# 1. Копируем собранные wheel-пакеты во временную папку
COPY packages/ /tmp/packages/

# 2. Копируем pyproject.toml и исходный код аналитика в рабочую директорию /app
COPY rag-platform-researcher/pyproject.toml .
COPY rag-platform-researcher/src ./src

# 3. Сначала ставим контракт из wheel, а затем аналитик в режиме редактирования (-e .)
# Мы используем "." потому что pyproject.toml лежит прямо в /app
RUN pip install --no-cache-dir /tmp/packages/rag_platform_contracts-1.0.0-py3-none-any.whl \
    /tmp/packages/rag_platform_observability-1.0.0-py3-none-any.whl \
    /tmp/packages/rag_platform_llm-1.0.0-py3-none-any.whl && \
    pip install -e .  --no-deps


# =========================================
# Runtime
# =========================================

FROM researcher-base AS runtime

ENV PYTHONPATH=/app/src
# 4. Запускаем uvicorn, указывая следить за изменениями в рабочей директории /app/src
CMD ["sh", "-c", "uvicorn rag_platform_researcher.main:app --host 0.0.0.0 --port $PORT --reload --reload-dir /app"]


# =========================================
# Shared Evaluation Base (Общий слой для оценки)
# =========================================
FROM researcher-base AS evaluation-shared-base

# Устанавливаем зависимости и копируем исходный код ОДИН раз
RUN pip install --no-cache-dir "psycopg[binary]"

COPY evaluation/researcher ./evaluation/researcher
COPY evaluation/common ./evaluation/common

ENV PYTHONPATH=/app/src


# =========================================
# Target 1: Evaluation (Запуск оценки)
# =========================================
FROM evaluation-shared-base AS evaluation

# Так как всё уже скопировано и настроено, пишем только команду запуска
CMD ["python", "-m", "evaluation.researcher.run_evaluation", "--mode", "smoke"]


# =========================================
# Target 2: Compare evaluation (Сравнение)
# =========================================
FROM evaluation-shared-base AS compare_evaluations

# Наследуемся от общей базы и переопределяем ENTRYPOINT
ENTRYPOINT ["python", "-m", "evaluation.researcher.compare_evaluations"]


