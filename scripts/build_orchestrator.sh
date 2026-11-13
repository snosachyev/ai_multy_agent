#!/bin/bash

set -e

echo "📦 Сборка rag-platform-orchestrator..."

cd rag-platform-orchestrator

rm -rf build dist *.egg-info

python -m build

cd ..

mkdir -p packages

cp rag-platform-orchestrator/dist/*.whl packages/

if [ "${SKIP_DOCKER:-0}" != "1" ]; then
    docker build --no-cache --target runtime -t rag-orchestrator:latest -f rag-platform-orchestrator/Dockerfile .
fi

echo "✅ Пакет собран и скопирован в packages/"