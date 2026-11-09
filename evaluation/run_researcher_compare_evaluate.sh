#!/bin/bash
set -euo pipefail

# Проверяем, что передано ровно 2 аргумента (два файла для сравнения)
if [ "$#" -ne 2 ]; then
    echo "❌ Ошибка: Вы должны передать два файла отчета для сравнения."
    echo "Использование: $0 путь/к/before.json путь/к/after.json"
    exit 1
fi

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
REPORTS_DIR="$PROJECT_ROOT/evaluation/researcher/reports"

IMAGE_NAME="researcher-evaluation"
DOCKER_NETWORK="rag-network"

# Извлекаем только имена файлов (например, evaluation_2026-11-07_07-04-34.json)
BEFORE_FILE_NAME=$(basename "$1")
AFTER_FILE_NAME=$(basename "$2")

# Формируем пути, какими они будут внутри Docker-контейнера
DOCKER_BEFORE_PATH="/app/evaluation/researcher/reports/$BEFORE_FILE_NAME"
DOCKER_AFTER_PATH="/app/evaluation/researcher/reports/$AFTER_FILE_NAME"

echo "📦 Запуск сравнения отчетов RAG..."
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
mkdir -p "$REPORTS_DIR"

# --------------------------------------------------
# Docker build
# --------------------------------------------------
echo "📦 Собираем docker..."
docker build \
    --target compare_evaluations \
    -f "$PROJECT_ROOT/rag-platform-researcher/Dockerfile" \
    -t "$IMAGE_NAME" \
    "$PROJECT_ROOT"

# --------------------------------------------------
# Docker run
# --------------------------------------------------
echo "Ожидаем 2 секунды для стабилизации..."
sleep 2

echo "📦 Запускаем сравнение файлов внутри Docker:"
echo "   - До: $DOCKER_BEFORE_PATH"
echo "   - После: $DOCKER_AFTER_PATH"

# Передаем трансформированные внутренние пути аргументами в самом конце docker run
docker run --rm \
    "$IMAGE_NAME" \
    "$DOCKER_BEFORE_PATH" \
    "$DOCKER_AFTER_PATH"

echo "✅ Сравнение завершено"
