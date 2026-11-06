"""
Модуль для сохранения результатов оценки работы оркестратора (Evaluation Runs) в базу данных.

Обеспечивает валидацию структуры отчета, сериализацию вложенных данных в формат JSON 
и безопасную запись в СУБД PostgreSQL с контролем транзакций и корректной обработкой исключений.

Зависимости:
    - psycopg: Для взаимодействия с базой данных PostgreSQL.
    - evaluation.common.postgres: Внутренний модуль для управления подключениями.
"""
from __future__ import annotations

import json
import psycopg

from evaluation.common.postgres import get_connection


def save_run(
    report: dict,
    connection: psycopg.Connection | None = None,
) -> None:
    """
    Сохраняет результаты одного запуска оценки оркестратора в базу данных.

    Если соединение `connection` передано извне, функция использует его и не закрывает.
    Если соединение не передано, функция самостоятельно создает новое соединение,
    фиксирует изменения и закрывает его перед выходом.

    Args:
        report (dict): Словарь со структурированными результатами запуска.
            Обязательные ключи: "run_id", "created_at", "git" (с подключом "commit"),
            "dataset" (с ключами "name", "questions"), "mode", "config" (с ключом
            "max_iterations"), "summary" (с метриками эффективности) и "results".
        connection (psycopg.Connection | None, optional): Существующее соединение
            с PostgreSQL. По умолчанию None.

    Raises:
        psycopg.Error: Возникает при сбоях на стороне СУБД или синтаксических ошибках SQL.
        TypeError: Возникает, если объект в `report["results"]` не может быть сериализован в JSON.
        ValueError: Возникает при некорректных значениях данных во время сериализации.
        KeyError: Может возникнуть на этапе распаковки, 
        если в `report` отсутствуют обязательные ключи.
    """
    owns_connection = connection is None

    if owns_connection:
        connection = get_connection()

    try:
        summary = report["summary"]
        dataset = report["dataset"]
        config = report["config"]

        # Сериализуем JSON заранее, чтобы в случае ошибки TypeError/ValueError 
        # не открывать транзакцию внутри блока cursor
        results_json = json.dumps(report["results"], ensure_ascii=False)

        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO orchestrator_evaluation_runs (
                    run_id,
                    created_at,
                    git_commit,
                    dataset,
                    mode,
                    questions_count,
                    max_iterations,
                    task_completion,
                    workflow_completed,
                    routing_success,
                    agent_execution_success_rate,
                    avg_iterations,
                    avg_agent_calls,
                    avg_errors,
                    avg_duration_ms,
                    results
                )
                VALUES (
                    %(run_id)s,
                    %(created_at)s,
                    %(git_commit)s,
                    %(dataset)s,
                    %(mode)s,
                    %(questions_count)s,
                    %(max_iterations)s,
                    %(task_completion)s,
                    %(workflow_completed)s,
                    %(routing_success)s,
                    %(agent_execution_success_rate)s,
                    %(avg_iterations)s,
                    %(avg_agent_calls)s,
                    %(avg_errors)s,
                    %(avg_duration_ms)s,
                    %(results)s
                )
                """,
                {
                    "run_id": report["run_id"],
                    "created_at": report["created_at"],
                    "git_commit": report["git"]["commit"],
                    "dataset": dataset["name"],
                    "mode": report["mode"],
                    "questions_count": dataset["questions"],
                    "max_iterations": config["max_iterations"],
                    "task_completion": summary["task_completion"],
                    "workflow_completed": summary["workflow_completed"],
                    "routing_success": summary["routing_success"],
                    "agent_execution_success_rate": summary["agent_execution_success_rate"],
                    "avg_iterations": summary["avg_iterations"],
                    "avg_agent_calls": summary["avg_agent_calls"],
                    "avg_errors": summary["avg_errors"],
                    "avg_duration_ms": summary["avg_duration_ms"],
                    "results": results_json,
                },
            )

        connection.commit()
        print("connection commit")

    except psycopg.Error as db_ex:
        print(f"Database error occurred: {db_ex}")
        if connection:
            connection.rollback()
    except (TypeError, ValueError) as json_ex:
        print(f"JSON serialization error: {json_ex}")
        if connection:
            connection.rollback()
    except KeyError as key_ex:
        print(f"Missing expected key in report dictionary: {key_ex}")
        if connection:
            connection.rollback()

    finally:
        if owns_connection and connection:
            connection.close()
