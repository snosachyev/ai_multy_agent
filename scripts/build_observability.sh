#!/bin/bash

set -e

echo "📦 Сборка rag-platform-observability..."

cd rag-platform-observability

rm -rf build dist *.egg-info

python -m build

cd ..

mkdir -p packages

cp rag-platform-observability/dist/*.whl packages/

echo "✅ Пакет собран и скопирован в packages/"