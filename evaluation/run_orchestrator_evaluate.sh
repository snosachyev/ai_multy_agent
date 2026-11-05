
#!/bin/bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
REPORTS_DIR="$PROJECT_ROOT/evaluation/orchestrator/reports"

IMAGE_NAME="orchestrator-evaluation"
DOCKER_NETWORK="rag-network"

echo "Starting Orchestrator evaluation..."

# Git commit
if git -C "$PROJECT_ROOT" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    GIT_COMMIT=$(git -C "$PROJECT_ROOT" rev-parse HEAD)
else
    GIT_COMMIT="unknown"
fi

echo "Git commit: $GIT_COMMIT"

# Reports directory
mkdir -p "$REPORTS_DIR"

# Build evaluation image
echo "Building evaluation image..."

docker build \
    --target evaluation \
    -f "$PROJECT_ROOT/rag-platform-orchestrator/Dockerfile" \
    -t "$IMAGE_NAME" \
    "$PROJECT_ROOT"

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

# Run evaluation
echo "Running evaluation..."

docker run --rm \
    --network "$DOCKER_NETWORK" \
    -e OLLAMA_BASE_URL="http://ollama-service:11434" \
    -e LOG_LEVEL=DEBUG \
    -e GIT_COMMIT="$GIT_COMMIT" \
    "${DOCKER_ENV_ARGS[@]+"${DOCKER_ENV_ARGS[@]}"}" \
    -v "$REPORTS_DIR:/app/evaluation/orchestrator/reports" \
    "$IMAGE_NAME"

echo "Evaluation completed."
echo "Reports: $REPORTS_DIR"
