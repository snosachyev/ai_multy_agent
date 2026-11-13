#!/bin/bash

set -e

# Переходим в папку с контрактами
cd rag-platform-contracts || exit

# Собираем проект
python -m build

# Возвращаемся в корневую директорию
cd ../

# Создаём корневую папку packages, если её нет
mkdir -p packages

# Копируем собранный wheel
cp rag-platform-contracts/dist/*.whl packages/

echo "Упаковка и копирование завершены успешно!"