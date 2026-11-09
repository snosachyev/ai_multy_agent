#!/bin/bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

REPORTS_DIR="$PROJECT_ROOT/evaluation/researcher/reports"

IMAGE_NAME="researcher-evaluation"
DOCKER_NETWORK="rag-network"

echo "📦 Запуск evaluation researcher..."
echo "📁 Project root: $PROJECT_ROOT"

# --------------------------------------------------
# Git commit
# --------------------------------------------------

if git -C "$PROJECT_ROOT" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    GIT_COMMIT=$(git -C "$PROJECT_ROOT" rev-parse HEAD 2>/dev/null || echo "unknown")
else
    GIT_COMMIT="unknown"
fi

echo "Git commit: ${GIT_COMMIT}"

# --------------------------------------------------
# Reports directory
# --------------------------------------------------

mkdir -p "$REPORTS_DIR"

# --------------------------------------------------
# Docker build
# --------------------------------------------------

echo "📦 Собираем docker..."

docker build \
    --target evaluation \
    -f "$PROJECT_ROOT/rag-platform-researcher/Dockerfile" \
    -t "$IMAGE_NAME" \
    "$PROJECT_ROOT"

# Динамический проброс переменных окружения для зависимых сервисов
DOCKER_ENV_ARGS=()
AGENT_VARS=(
    "DIRECTOR_SERVICE_URL"
    "RESEARCHER_SERVICE_URL"
    "ANALYST_SERVICE_URL"
    "FINALIZER_SERVICE_URL"
)

for var in "${AGENT_VARS[@]}"; do
    # Конструкция ${!var+x} проверяет, объявлена ли переменная (даже если пустая),
    # а ${!var:-} безопасно извлекает значение или пустую строку, не триггеря флаг -u
    if [ -n "${!var+x}" ] && [ -n "${!var:-}" ]; then
        echo "🔹 Обнаружена переменная $var, пробрасываем в Docker: ${!var}"
        DOCKER_ENV_ARGS+=("-e" "$var=${!var}")
    fi
done

# --------------------------------------------------
# Docker run
# --------------------------------------------------

echo "Ожидаем 5 секунд для стабилизации..."
sleep 5

echo "📦 Запускаем docker..."

docker run --rm \
    --network "$DOCKER_NETWORK" \
    -e HF_HUB_DISABLE_TELEMETRY=1 \
    -e HF_HUB_ENABLE_HF_TRANSFER=0 \
    -e TRANSFORMERS_OFFLINE=1 \
    -e HF_HUB_OFFLINE=1 \
    -e HF_HUB_DISABLE_SYMLINKS_WARNING=1 \
    -e HTTPX_TIMEOUT=5.0 \
    -e OLLAMA_BASE_URL="http://ollama-service:11434" \
    -e LLM_MODEL=qwen2.5:7b \
    -e PROVIDER=ollama \
    -e PORT=8000 \
    -e PYTHONUNBUFFERED=1 \
    -e LOG_LEVEL=DEBUG \
    -e DATA_DIR="/app/data" \
    -e GIT_COMMIT="${GIT_COMMIT}" \
    ${DOCKER_ENV_ARGS[@]+"${DOCKER_ENV_ARGS[@]}"} \
    -v "$REPORTS_DIR:/app/evaluation/researcher/reports" \
    -v "${PROJECT_ROOT}/data:/app/data" \
    -v "$HOME/.cache/huggingface:/root/.cache/huggingface" \
    "$IMAGE_NAME"

echo "✅ Evaluation завершён"
echo "📊 Reports: $REPORTS_DIR"
