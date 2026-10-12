#!/bin/bash

# Переходим в папку с контрактами
cd rag-platform-contracts || exit

# Собираем проект (создаем .whl файл)
python -m build

# Копируем собранный пакет во внутреннюю папку packages
cp dist/*.whl packages/

# Возвращаемся в исходную директорию
cd ../

# Копируем собранный пакет в корневую папку packages
cp rag-platform-contracts/dist/*.whl packages/

echo "Упаковка и копирование завершены успешно!"
