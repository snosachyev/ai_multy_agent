FROM ghcr.io/snosachyev/rag-python-base:latest

WORKDIR /app

# Копируем общий пакет контрактов и зависимости
COPY packages/rag_platform_contracts-*.whl /tmp/
COPY requirements-vector.txt .

RUN pip install --no-cache-dir /tmp/rag_platform_contracts-*.whl && \
    pip install --no-cache-dir -r requirements-vector.txt

# Копируем код ETL-сервиса
COPY rag-platform-ingestion/src /app/src

ENV PYTHONPATH=/app/src

ENTRYPOINT ["python", "-m", "rag_platform_ingestion.ingest"]
