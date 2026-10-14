#!/bin/bash

set -e

echo "📦 Сборка rag-platform-researcher..."

cd rag-platform-researcher

rm -rf build dist *.egg-info

python -m build

cd ..

mkdir -p packages

cp rag-platform-researcher/dist/*.whl packages/

docker build --no-cache -t rag-researcher:latest -f rag-platform-researcher/Dockerfile .

echo "✅ Пакет собран и скопирован в packages/"