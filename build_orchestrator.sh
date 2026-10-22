#!/bin/bash

set -e

echo "📦 Сборка rag-platform-orchestrator..."

cd rag-platform-orchestrator

rm -rf build dist *.egg-info

python -m build

cd ..

mkdir -p packages

cp rag-platform-orchestrator/dist/*.whl packages/

docker build --no-cache -t rag-orchestrator:latest -f rag-platform-orchestrator/Dockerfile .

echo "✅ Пакет собран и скопирован в packages/"