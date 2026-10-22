# docker/rag-python-base.Dockerfile
FROM python:3.12-slim

WORKDIR /app

RUN pip install --upgrade sentence-transformers