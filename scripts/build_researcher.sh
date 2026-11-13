#!/bin/bash

set -e

echo "📦 Сборка rag-platform-researcher..."

cd rag-platform-researcher

rm -rf build dist *.egg-info

python -m build

cd ..

mkdir -p packages

cp rag-platform-researcher/dist/*.whl packages/

if [ "${SKIP_DOCKER:-0}" != "1" ]; then
    docker build --no-cache --target runtime  -t rag-researcher:latest -f rag-platform-researcher/Dockerfile .
fi

echo "✅ Пакет собран и скопирован в packages/"