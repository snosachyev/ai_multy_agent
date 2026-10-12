#!/bin/bash

set -e

echo "📦 Сборка rag_platform_llm..."

cd rag-platform-llm

rm -rf build dist *.egg-info

python -m build

cd ..

mkdir -p packages

cp rag-platform-llm/dist/*.whl packages/

echo "✅ Пакет собран и скопирован в packages/"