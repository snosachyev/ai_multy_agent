#!/bin/bash

set -e

echo "📦 Сборка rag-platform-analyst..."

cd rag-platform-analyst

rm -rf build dist *.egg-info

python -m build

cd ..

mkdir -p packages

cp rag-platform-analyst/dist/*.whl packages/

docker build --no-cache -t rag-analyst:latest -f rag-platform-analyst/Dockerfile .

echo "✅ Пакет собран и скопирован в packages/"