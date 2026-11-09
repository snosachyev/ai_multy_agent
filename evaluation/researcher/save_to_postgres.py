"""Модуль для сохранения результатов оценки работы ресерчера 
(Researcher Evaluation Runs) в базу данных.

Обеспечивает валидацию структуры отчета с помощью Pydantic, извлечение динамических
метрики, а также безопасную запись в СУБД PostgreSQL с контролем транзакций и зеркальной 
оркестратору обработкой исключений.

Зависимости:
    - psycopg: Для взаимодействия с базой данных PostgreSQL.
    - evaluation.common.postgres: Внутренний модуль для управления подключениями.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import UUID, uuid4

import psycopg
from pydantic import BaseModel, Field, ValidationError

from evaluation.common.postgres import get_connection


class ResearcherEvaluationRun(BaseModel):
    """Pydantic-модель для валидации и структурирования данных запуска оценки ресерчера."""

    run_id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    git_commit: Optional[str] = None
    dataset: str
    mode: str

    # Конфигурация RAG
    embedding_model: str
    llm_model: str
    chunk_size: int
    chunk_overlap: int
    top_k: int
    questions_count: int

    # Метрики RAG
    recall_at_5: float
    precision_at_5: float
    mrr: float
    faithfulness: float
    relevance: float
    correctness: float

    def to_dict_for_sql(self) -> Dict[str, Any]:
        """Экспорт словаря с приведением типов для подстановки в execute."""
        data = self.model_dump()
        data["run_id"] = str(data["run_id"])
        return data


def save_run(
    report: dict,
    connection: psycopg.Connection | None = None,
) -> None:
    """Сохраняет результаты одного запуска оценки ресерчера в базу данных PostgreSQL.

    Если соединение `connection` передано извне, функция использует его и не закрывает.
    Если соединение не передано, функция самостоятельно создает новое соединение,
    фиксирует изменения и закрывает его перед выходом.

    Args:
        report (dict): Словарь со структурированными результатами запуска.
        connection (psycopg.Connection | None, optional): Существующее соединение
            с PostgreSQL. По умолчанию None.

    Raises:
        psycopg.Error: Возникает при сбоях на стороне СУБД или синтаксических ошибках SQL.
        ValidationError: Возникает при ошибке валидации данных Pydantic-моделью.
        KeyError: Может возникнуть на этапе распаковки, если в `report` отсутствуют
        обязательные ключи.
    """
    owns_connection = connection is None

    if owns_connection:
        connection = get_connection()

    try:
        summary = report["summary"]
        retrieval = summary.get("retrieval", {})
        generation = summary.get("generation", {})
        config = report["config"]
        dataset = report["dataset"]

        top_k = config.get("top_k", 5)

        # Безопасно извлекаем метрики с поддержкой динамических ключей (recall_at_X)
        # и защитой от отсутствия генерации в режиме "retrieval"
        recall_val = retrieval.get(f"recall_at_{top_k}", retrieval.get("recall_at_5", 0.0))
        precision_val = retrieval.get(f"precision_at_{top_k}", retrieval.get("precision_at_5", 0.0))
        mrr_val = retrieval.get("mrr", 0.0)

        faithfulness_val = generation.get("faithfulness", 0.0) if generation else 0.0
        relevance_val = generation.get("relevance", 0.0) if generation else 0.0
        correctness_val = generation.get("correctness", 0.0) if generation else 0.0

        # Инициализируем Pydantic-модель для валидации данных перед транзакцией
        run_data = ResearcherEvaluationRun(
            run_id=report["run_id"],
            created_at=report["created_at"],
            git_commit=report["git"]["commit"],
            dataset=dataset["name"],
            mode=report["mode"],
            embedding_model=config["embedding_model"],
            llm_model=config["llm_model"],
            chunk_size=config["chunk_size"],
            chunk_overlap=config["chunk_overlap"],
            top_k=top_k,
            questions_count=dataset["questions_count"],
            recall_at_5=recall_val,
            precision_at_5=precision_val,
            mrr=mrr_val,
            faithfulness=faithfulness_val,
            relevance=relevance_val,
            correctness=correctness_val,
        )

        insert_query = """
            INSERT INTO researcher_evaluation_runs (
                run_id, created_at, git_commit, dataset, mode,
                embedding_model, llm_model, chunk_size, chunk_overlap, top_k,
                questions_count, recall_at_5, precision_at_5, mrr,
                faithfulness, relevance, correctness
            )
            VALUES (
                %(run_id)s, %(created_at)s, %(git_commit)s, %(dataset)s, %(mode)s,
                %(embedding_model)s, %(llm_model)s, %(chunk_size)s, %(chunk_overlap)s, %(top_k)s,
                %(questions_count)s, %(recall_at_5)s, %(precision_at_5)s, %(mrr)s,
                %(faithfulness)s, %(relevance)s, %(correctness)s
            )
        """

        with connection.cursor() as cursor:
            cursor.execute(insert_query, run_data.to_dict_for_sql())

        connection.commit()
        print("connection commit")

    except psycopg.Error as db_ex:
        print(f"Database error occurred: {db_ex}")
        if connection:
            connection.rollback()
    except ValidationError as val_ex:
        print(f"Pydantic validation error: {val_ex}")
        if connection:
            connection.rollback()
    except KeyError as key_ex:
        print(f"Missing expected key in report dictionary: {key_ex}")
        if connection:
            connection.rollback()

    finally:
        if owns_connection and connection:
            connection.close()
