#!/bin/bash

set -e

echo "📦 Сборка rag-platform-director..."

cd rag-platform-director

rm -rf build dist *.egg-info

python -m build

cd ..

mkdir -p packages

cp rag-platform-director/dist/*.whl packages/

docker build --no-cache -t rag-director:latest -f rag-platform-director/Dockerfile .

echo "✅ Пакет собран и скопирован в packages/"