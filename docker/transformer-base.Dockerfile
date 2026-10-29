
FROM python:3.12-slim

WORKDIR /app

ENV PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Только CPU-версия PyTorch
RUN python -m pip install --no-cache-dir \
    torch==2.7.1 \
    --index-url https://download.pytorch.org/whl/cpu

# Остальные зависимости
RUN python -m pip install --no-cache-dir \
    sentence-transformers
