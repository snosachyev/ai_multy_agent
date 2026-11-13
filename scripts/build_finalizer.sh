#!/bin/bash

set -e

echo "📦 Сборка rag-platform-finalizer..."

cd rag-platform-finalizer

rm -rf build dist *.egg-info

python -m build

cd ..

mkdir -p packages

cp rag-platform-finalizer/dist/*.whl packages/

if [ "${SKIP_DOCKER:-0}" != "1" ]; then
    docker build --no-cache -t rag-finalizer:latest -f rag-platform-finalizer/Dockerfile .
fi

echo "✅ Пакет собран и скопирован в packages/"