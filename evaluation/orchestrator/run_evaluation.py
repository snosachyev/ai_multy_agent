"""Модуль запуска и проведения эвалюации (оценки качества) Оркестратора.

Обеспечивает загрузку тестовых датасетов (Smoke или Full), итерационный прогон
тестовых вопросов через движок мультиагентного воркфлоу, замер временных метрик
и последующую передачу агрегированных результатов для сохранения в PostgreSQL.
"""
from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

import asyncio
import json
import logging
import os
import time
import uuid
import httpx
import psycopg

from rag_platform_orchestrator.presentation.dependencies import (
    get_workflow,
)

from evaluation.orchestrator.metrics import (
    agent_calls,
    agent_execution_success_rate,
    errors_count,
    iterations,
    routing_success,
    task_completion,
    workflow_completed,
)
from evaluation.orchestrator.save_to_postgres import (
    save_run,
)

from evaluation.common.postgres import (
    get_connection,
)


logger = logging.getLogger(__name__)


BASE_DIR = Path(__file__).resolve().parent

DATASETS_DIR = BASE_DIR / "datasets"
REPORTS_DIR = BASE_DIR / "reports"

SMOKE_DATASET = (
    DATASETS_DIR / "orchestrator_eval_smoke.json"
)

FULL_DATASET = (
    DATASETS_DIR / "orchestrator_eval.json"
)


def load_dataset(path: Path) -> list[dict]:
    """Загружает тестовый датасет из указанного JSON-файла.

    Args:
        path (Path): Абсолютный или относительный путь к файлу датасета.

    Returns:
        list[dict]: Список словарей, где каждый словарь представляет собой
            отдельный тестовый случай (например, вопрос и ожидаемый ответ).
    """
    with open(
        path,
        encoding="utf-8",
    ) as file:
        return json.load(file)


def average(values: list[float]) -> float:
    """Вычисляет среднее арифметическое для списка числовых значений.

    Защищает от ошибки деления на ноль (ZeroDivisionError), возвращая 0.0
    для пустых списков.

    Args:
        values (list[float]): Список чисел с плавающей точкой.

    Returns:
        float: Среднее значение или 0.0, если список пуст.
    """
    if not values:
        return 0.0

    return sum(values) / len(values)


async def evaluate_question(
    workflow,
    item: dict,
    max_iterations: int,
) -> dict:
    """Асинхронно тестирует один вопрос на инстансе воркфлоу Оркестратора.

    Выполняет замер времени обработки запроса (в миллисекундах) с помощью
    высокоточного таймера `time.perf_counter()`.

    Args:
        workflow: Экземпляр (инстанс) запущенного воркфлоу Оркестратора,
            у которого вызывается метод `run`.
        item (dict): Словарь с тестовыми данными, содержащий ключ "question".
        max_iterations (int): Максимально допустимое количество итераций
            (шагов) для агентов внутри одного запуска.

    Returns:
        dict: Словарь, содержащий результаты работы воркфлоу и метаданные
            (включая `duration_ms`).
    """
    started_at = time.perf_counter()

    result = await workflow.run(
        user_input=item["question"],
        max_iterations=max_iterations,
    )

    duration_ms = (
        time.perf_counter() - started_at
    ) * 1000

    return {
        "id": item["id"],

        "question": item["question"],

        "reference_answer": item.get(
            "reference_answer"
        ),

        "task_completion": task_completion(
            result
        ),

        "workflow_completed": workflow_completed(
            result
        ),

        "routing_success": routing_success(
            result
        ),

        "agent_execution_success_rate": (
            agent_execution_success_rate(
                result
            )
        ),

        "iterations": iterations(
            result
        ),

        "agent_calls": agent_calls(
            result
        ),

        "errors_count": errors_count(
            result
        ),

        "duration_ms": round(
            duration_ms,
            2,
        ),

        "final_answer": result.get(
            "final_answer"
        ),

        "agent_results": result.get(
            "agent_results",
            [],
        ),

        "errors": result.get(
            "errors",
            [],
        ),
    }


def build_report(
    results: list[dict],
    dataset_path: Path,
    mode: str,
    max_iterations: int,
) -> dict:
    """Формирует итоговый агрегированный отчет по результатам эвалюации.

    Генерирует уникальный идентификатор запуска (UUID), фиксирует текущее время,
    собирает информацию о Git-коммите из переменных окружения и упаковывает
    все метрики в единую структуру (словарь) для последующей выгрузки 
    в отчет или сохранения в PostgreSQL.

    Args:
        results (list[dict]): Список словарей с результатами обработки каждого 
            отдельного вопроса из функции `evaluate_question`.
        dataset_path (Path): Путь к файлу датасета, на котором проводилось тестирование.
        mode (str): Режим запуска эвалюации (например, "smoke" или "full").
        max_iterations (int): Настройка лимита итераций, с которой запускался воркфлоу.

    Returns:
        dict: Структурированный отчет, содержащий метаданные запуска, 
            параметры окружения и агрегированные метрики производительности/качества.
    """
    return {
        "run_id": str(
            uuid.uuid4()
        ),

        "created_at": (
            datetime.now().isoformat()
        ),

        "git": {
            "commit": os.getenv(
                "GIT_COMMIT",
                "unknown",
            ),
        },

        "dataset": {
            "name": dataset_path.name,
            "questions": len(results),
        },

        "mode": mode,

        "config": {
            "max_iterations": max_iterations,
        },

        "summary": {
            "task_completion": average(
                [
                    item["task_completion"]
                    for item in results
                ]
            ),

            "workflow_completed": average(
                [
                    item["workflow_completed"]
                    for item in results
                ]
            ),

            "routing_success": average(
                [
                    item["routing_success"] 
                    for item in results
                ]
            ),

            "agent_execution_success_rate": (
                average(
                    [
                        item[
                            "agent_execution_success_rate"
                        ]
                        for item in results
                    ]
                )
            ),

            "avg_iterations": average(
                [
                    item["iterations"]
                    for item in results
                ]
            ),

            "avg_agent_calls": average(
                [
                    item["agent_calls"]
                    for item in results
                ]
            ),

            "avg_errors": average(
                [
                    item["errors_count"]
                    for item in results
                ]
            ),

            "avg_duration_ms": average(
                [
                    item["duration_ms"]
                    for item in results
                ]
            ),

            "successful_questions": sum(
                1
                for item in results
                if item["workflow_completed"]
                == 1.0
            ),
        },

        "results": results,
    }


def save_report(
    report: dict,
) -> Path:
    """Сохраняет сформированный отчет в файл формата JSON.

    Автоматически создает директорию для отчетов (включая родительские папки),
    если она еще не существует. Имя файла генерируется на основе уникального
    идентификатора `run_id` из отчета.

    Args:
        report (dict): Словарь с полными результатами и метаданными эвалюации.

    Returns:
        Path: Абсолютный путь к созданному JSON-файлу отчета.
    """
    REPORTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    path = (
        REPORTS_DIR
        / f"{report['run_id']}.json"
    )

    with open(
        path,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            report,
            file,
            ensure_ascii=False,
            indent=2,
        )

    latest = (
        REPORTS_DIR / "latest.json"
    )

    with open(
        latest,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            report,
            file,
            ensure_ascii=False,
            indent=2,
        )

    return path


def print_summary(
    report: dict,
) -> None:
    """Выводит краткую сводку по результатам эвалюации в консоль.

    Форматирует ключевые метрики (точность, время работы, количество вызовов)
    и записывает их в логгер с уровнем INFO для удобного чтения в терминале 
    или логах пайплайна CI/CD.

    Args:
        report (dict): Словарь с результатами эвалюации, содержащий секцию "summary".
    """
    summary = report["summary"]

    logger.info("=" * 80)
    logger.info(
        "ORCHESTRATOR EVALUATION SUMMARY"
    )
    logger.info("=" * 80)

    logger.info(
        "Questions: %d",
        report["dataset"]["questions"],
    )

    logger.info(
        "Task completion: %.3f",
        summary[
            "task_completion"
        ],
    )

    logger.info(
        "Workflow completed: %.3f",
        summary[
            "workflow_completed"
        ],
    )

    logger.info(
        "Agent execution success: %.3f",
        summary[
            "agent_execution_success_rate"
        ],
    )

    logger.info(
        "Average iterations: %.3f",
        summary[
            "avg_iterations"
        ],
    )

    logger.info(
        "Average agent calls: %.3f",
        summary[
            "avg_agent_calls"
        ],
    )

    logger.info(
        "Average errors: %.3f",
        summary[
            "avg_errors"
        ],
    )

    logger.info(
        "Average duration: %.2f ms",
        summary[
            "avg_duration_ms"
        ],
    )

    logger.info(
        "Successful questions: %d/%d",
        summary[
            "successful_questions"
        ],
        report["dataset"]["questions"],
    )

    logger.info("=" * 80)


async def main() -> None:
    """Главная точка входа для запуска процесса эвалюации Оркестратора.

    Инициализирует парсер аргументов командной строки, настраивает конфигурацию
    запуска (выбор датасета, лимиты), разворачивает асинхронный воркфлоу,
    координирует запуск тестов, агрегацию результатов, их логирование, 
    сохранение на диск и отправку в базу данных PostgreSQL.
    """
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--mode",
        choices=[
            "smoke",
            "full",
        ],
        default="smoke",
    )

    parser.add_argument(
        "--no-db",
        action="store_true",
        help=(
            "Do not save evaluation "
            "result to PostgreSQL"
        ),
    )

    args = parser.parse_args()

    if args.mode == "smoke":
        dataset_path = SMOKE_DATASET
    else:
        dataset_path = FULL_DATASET

    dataset = load_dataset(
        dataset_path
    )

    max_iterations = int(
        os.getenv(
            "MAX_ITERATIONS",
            "3",
        )
    )

    logger.info(
        "Loading workflow from production factory"
    )

    timeout = httpx.Timeout(
        connect=10.0,
        read=300.0,
        write=30.0,
        pool=10.0,
    )

    async with httpx.AsyncClient(timeout=timeout) as http_client:
        workflow = get_workflow(http_client)

        # Здесь должен находиться код evaluation,
        # который использует workflow.

        results: list[dict] = []

        for item in dataset:

            logger.info(
                "Evaluating %s: %s",
                item["id"],
                item["question"],
            )

            result = await evaluate_question(
                workflow=workflow,
                item=item,
                max_iterations=max_iterations,
            )

            results.append(result)

            logger.info(
                "Completed %s in %.2f ms",
                item["id"],
                result["duration_ms"],
            )

        report = build_report(
            results=results,
            dataset_path=dataset_path,
            mode=args.mode,
            max_iterations=max_iterations,
        )

        print_summary(report)

        path = save_report(
            report
        )

        logger.info(
            "Report saved to %s",
            path,
        )

        if not args.no_db:
            with get_connection() as connection:
                connection: psycopg.Connection
                save_run(report, connection=connection)

                logger.info(
                    "Evaluation saved to PostgreSQL to table orchestrator_evaluation_runs"
                )


if __name__ == "__main__":
    asyncio.run(main())
