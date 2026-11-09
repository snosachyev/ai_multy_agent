"""Основной скрипт для автоматизированной оценки (evaluation) качества работы RAG-платформы."""

import argparse
import asyncio
import json
import shutil
import os
import psycopg
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


# Инфраструктура платформы
from rag_platform_observability.observability import configure_logging, get_logger
from rag_platform_researcher.config.settings import settings
from rag_platform_researcher.dependencies import get_llm, get_query_generator, get_rag_service
from rag_platform_researcher.infrastructure.rag.chroma import ChromaVectorStore

# Метрики и утилиты
from evaluation.common.postgres import get_connection
from evaluation.researcher.metrics import average
from evaluation.researcher.save_to_postgres import save_run
from evaluation.researcher.retrieval.mrr import reciprocal_rank
from evaluation.researcher.retrieval.precision import precision_at_k
from evaluation.researcher.retrieval.recall import recall_at_k
from evaluation.researcher.generation.evaluator import evaluate_generation


DATASET_PATH = Path(__file__).parent / "datasets" / "rag_eval.json"

K = 5
EMBEDDING_MODEL = "intfloat/multilingual-e5-base"
LLM_MODEL = "qwen2.5:7b"

CHUNK_SIZE = 512
CHUNK_OVERLAP = 50

configure_logging()

logger = get_logger(__name__)

DEBUG_RAG = os.getenv("DEBUG_RAG", "false").lower() == "true"

REPORTS_DIR = Path(__file__).parent / "reports"


def parse_args() -> argparse.Namespace:
    """Парсит аргументы командной строки для выбора режима оценки.

    Returns:
        argparse.Namespace: Спарсенные аргументы запуска.
    """
    parser = argparse.ArgumentParser(description="RAG Platform Evaluation CLI")
    parser.add_argument(
        "--mode",
        choices=["smoke", "retrieval", "full"],
        default="smoke",
        help="Режим работы пайплайна оценки.",
    )

    parser.add_argument(
        "--no-db",
        action="store_true",
        help=(
            "Do not save evaluation "
            "result to PostgreSQL"
        ),
    )
    return parser.parse_args()


def save_report(report: dict) -> Path:
    """Сохраняет финальный отчет оценки в формате JSON на диск.

    Функция создаёт директорию для отчетов (если она отсутствует), записывает 
    уникальный файл отчета с временной меткой в названии, а также перезаписывает 
    файл `latest.json`, содержащий актуальную копию самого последнего прогона.

    Args:
        report (dict): Словарь с результатами оценки (конфигурация, метрики, детали).

    Returns:
        Path: Абсолютный или относительный путь к созданному файлу отчета с временной меткой.
    """
    REPORTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    # Рефакторинг: Использование timezone.utc гарантирует консистентность дат на любых серверах
    timestamp = datetime.now(timezone.utc).strftime(
        "%Y-%m-%d_%H-%M-%S"
    )

    report_path = (
        REPORTS_DIR /
        f"evaluation_{timestamp}.json"
    )

    latest_path = REPORTS_DIR / "latest.json"

    # Записываем основной файл отчета
    with open(
        report_path,
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(
            report,
            f,
            ensure_ascii=False,
            indent=2,
        )

    # Рефакторинг: Вместо повторной тяжелой сериализации через json.dump в `latest.json`,
    # гораздо быстрее скопировать уже готовый файл на диске с помощью shutil.copy2
    try:
        shutil.copy2(report_path, latest_path)
    except IOError as e:
        logger.warning("Failed to update latest.json via copy: %s", e)

    logger.info(
        "Evaluation report saved: %s",
        report_path,
    )

    return report_path


async def evaluate_item(item: Dict[str, Any], rag_service: Any, mode: str) -> Dict[str, Any]:
    """Проводит полную асинхронную оценку для одного элемента датасета.

    Args:
        item: Тестовый пример из датасета со всеми метаданными.
        rag_service: Инициализированный инстанс RAG-пайплайна.
        mode: Выбранный режим работы (smoke/retrieval/full).

    Returns:
        Dict[str, Any]: Результаты расчетов метрик для конкретного вопроса.
    """
    question = item["question"]
    # Динамически берем топ-K документов из настроек, иначе fallback на 5
    top_k = getattr(settings, "top_k", 5)

    if DEBUG_RAG:
        logger.debug("\n%s\nQUESTION: %s\n%s", "=" * 80, question, "=" * 80)

    # Шаг 1: Выполнение RAG-запроса
    result = await rag_service.execute(question)

    retrieved_ids = [document.id for document in result.documents]
    relevant_ids = item["relevant_documents"]

    # Шаг 2: Расчет базовых метрик ретривала
    recall = recall_at_k(retrieved_ids=retrieved_ids, relevant_ids=relevant_ids, k=top_k)
    precision = precision_at_k(retrieved_ids=retrieved_ids, relevant_ids=relevant_ids, k=top_k)
    rr = reciprocal_rank(retrieved_ids=retrieved_ids, relevant_ids=relevant_ids)

    retrieval_result = {
        "id": item["id"],
        "question": question,
        "recall_at_k": recall,
        "precision_at_k": precision,
        "reciprocal_rank": rr,
    }

    generation_result = None

    # Шаг 3: Расчет метрик генерации (если выбран полный цикл оценки)
    if mode != "retrieval":
        generation = await evaluate_generation(
            llm=rag_service.llm,
            question=question,
            context=result.context,
            answer=result.answer,
            reference_answer=item.get("reference_answer"),
        )

        generation_result = {
            "id": item["id"],
            "question": question,
            **generation,
        }

        if DEBUG_RAG:
            logger.debug(
                "\nRecall@%d:     %.3f\nPrecision@%d:  %.3f\nMRR:             %.3f",
                top_k, recall, top_k, precision, rr
            )
            logger.debug("Faithfulness:  %.3f", generation["faithfulness"]["score"])
            logger.debug("Relevance:     %.3f", generation["relevance"]["score"])
            if "correctness" in generation:
                logger.debug("Correctness:   %.3f", generation["correctness"]["score"])

    return {
        "retrieval": retrieval_result,
        "generation": generation_result
    }


async def main() -> None:
    """Главная управляющая функция асинхронного пайплайна оценки RAG."""
    args = parse_args()

    # Выбор пути к датасету на основе переданного аргумента
    if args.mode == "smoke":
        dataset_path = Path(__file__).parent / "datasets" / "rag_eval_smoke.json"
    else:
        dataset_path = Path(__file__).parent / "datasets" / "rag_eval.json"

    with open(dataset_path, "r", encoding="utf-8") as f:
        dataset = json.load(f)

    logger.info(
        "Starting evaluation: mode=%s, dataset=%s, questions=%d",
        args.mode,
        dataset_path,
        len(dataset),
    )

    # Инициализация инфраструктуры и компонентов ядра RAG
    vector_store = ChromaVectorStore(splits_path=str(settings.splits_path))
    llm = get_llm()
    query_generator = get_query_generator(llm=llm)

    rag_service = get_rag_service(
        vector_store=vector_store,
        query_generator=query_generator,
        llm=llm
    )

    # Конкурентный запуск обработки всех элементов датасета через asyncio.gather
    tasks = [evaluate_item(item, rag_service, args.mode) for item in dataset]
    evaluated_items = await asyncio.gather(*tasks)

    # Разбираем результаты по соответствующим спискам
    retrieval_results = [item["retrieval"] for item in evaluated_items]
    generation_results = [
        item["generation"] for item in evaluated_items if item["generation"] is not None
    ]

    # Сборка и визуализация отчета вашими функциями
    report = build_report(
        retrieval_results=retrieval_results,
        generation_results=generation_results,
        dataset_path=dataset_path,
        mode=args.mode,
        questions_count=len(dataset),
    )

    print_summary(report)
    save_report(report)

    # Сохранение результатов в PostgreSQL
    if not args.no_db:  # Привели к единому флагу, если он используется
        try:
            with get_connection() as connection:
                connection: psycopg.Connection
                save_run(report, connection=connection)
                logger.info("Evaluation saved to PostgreSQL to table orchestrator_evaluation_runs")
        except psycopg.Error as e:  # Рефакторинг: ловим только специфичные для PostgreSQL ошибки
            logger.error("Failed to save evaluation run to PostgreSQL due to database error: %s", e)



def average_generation(results: List[Dict[str, Any]], metric: str) -> float:
    """Вычисляет средний балл для заданной метрики генерации по всем результатам.

    Функция собирает оценки (`score`) для указанной метрики (например, "faithfulness", 
    "relevance", "correctness") из списка результатов и рассчитывает их среднее 
    арифметическое. Если метрика отсутствует в данных или список пуст, возвращается `0.0`.

    Args:
        results (List[Dict[str, Any]]): Список словарей с результатами оценки генерации 
            для каждого тестового примера.
        metric (str): Название метрики, для которой необходимо рассчитать средний балл.

    Returns:
        float: Среднее значение метрики в диапазоне [0.0, 1.0].
    """
    values = [
        item[metric]["score"]
        for item in results
        if metric in item 
        and isinstance(item[metric], dict)   # Рефакторинг: защита от некорректного типа данных
        and "score" in item[metric]         # Рефакторинг: защита от отсутствия ключа score
    ]

    if not values:
        return 0.0

    return sum(values) / len(values)


def build_report(
    retrieval_results: List[Dict[str, Any]],
    generation_results: List[Dict[str, Any]],
    dataset_path: Path,
    mode: str,
    questions_count: int,
) -> Dict[str, Any]:
    """Формирует итоговый структурированный отчет по результатам оценки RAG.

    Собирает воедино метаданные запуска (Git-коммит, режим, датасет), конфигурацию 
    компонентов системы (модели, параметры чанкинга) и агрегированные средние 
    метрики для поиска (retrieval) и генерации (generation).

    Args:
        retrieval_results (List[Dict[str, Any]]): Детальные результаты оценки поиска.
        generation_results (List[Dict[str, Any]]): Детальные результаты оценки генерации.
        dataset_path (Path): Путь к файлу использованного тестового датасета.
        mode (str): Режим проведения оценки (например, "smoke", "retrieval", "full").
        questions_count (int): Общее количество вопросов в прогоне.

    Returns:
        Dict[str, Any]: Словарь, представляющий собой полный отчет для сохранения или отправки в БД.
    """
    # Рефакторинг: извлекаем параметры динамически, приоритет — у настроек и окружения (.env)
    llm_model_name = getattr(settings, "llm_model", os.getenv("LLM_MODEL", "qwen2.5:7b"))
    embedding_model_name = getattr(
        settings, "embedding_model", os.getenv("EMBEDDING_MODEL", "intfloat/multilingual-e5-base")
    )
    top_k = getattr(settings, "top_k", 5)
    chunk_size = getattr(settings, "chunk_size", 512)
    chunk_overlap = getattr(settings, "chunk_overlap", 50)

    return {
        "run_id": str(uuid.uuid4()),

        # Рефакторинг: Использование явного UTC для корректной временной метки изоформата
        "created_at": datetime.now(timezone.utc).isoformat(),

        "git": {
            "commit": os.getenv("GIT_COMMIT", "unknown"),
        },

        "dataset": {
            "name": dataset_path.name,
            "questions_count": questions_count,
        },

        "mode": mode,

        "config": {
            "embedding_model": embedding_model_name,
            "llm_model": llm_model_name,
            "chunk_size": chunk_size,
            "chunk_overlap": chunk_overlap,
            "top_k": top_k,
            "provider": os.getenv("PROVIDER", "ollama"),
            "ollama_base_url": os.getenv("OLLAMA_BASE_URL", "http://ollama-service:11434"),
        },

        "summary": {
            "retrieval": {
                f"recall_at_{top_k}": average(
                    retrieval_results,
                    "recall_at_k",
                ),
                f"precision_at_{top_k}": average(
                    retrieval_results,
                    "precision_at_k",
                ),
                "mrr": average(
                    retrieval_results,
                    "reciprocal_rank",
                ),
            },

            "generation": {
                "faithfulness": average(
                    generation_results,
                    "faithfulness",
                ),
                "relevance": average(
                    generation_results,
                    "relevance",
                ),
                "correctness": average(
                    generation_results,
                    "correctness",
                ),
            },
        },

        "retrieval_results": retrieval_results,
        "generation_results": generation_results,
    }


def print_summary(report: dict) -> None:
    """Выводит агрегированную информацию о результатах оценки RAG в логи.

    Функция форматирует и записывает в логгер сводные данные по метрикам 
    поиска (Recall, Precision, MRR) и генерации (Faithfulness, Relevance, 
    Correctness, если они присутствуют в отчете).

    Args:
        report (dict): Итоговый структурированный словарь-отчет, 
            сгенерированный функцией `build_report`.

    Returns:
        None
    """
    summary = report["summary"]

    retrieval = summary["retrieval"]
    generation = summary["generation"]

    # Динамически получаем K для точного определения ключей в словаре отчета
    top_k = report["config"]["top_k"]

    logger.info("=" * 80)
    logger.info("RAG EVALUATION SUMMARY")
    logger.info("=" * 80)

    # Рефакторинг: используем f-строки для поиска динамического ключа вида 'recall_at_5'
    logger.info(
        "Recall@%d: %.3f",
        top_k,
        retrieval.get(f"recall_at_{top_k}", 0.0),
    )

    logger.info(
        "Precision@%d: %.3f",
        top_k,
        retrieval.get(f"precision_at_{top_k}", 0.0),
    )

    logger.info(
        "MRR: %.3f",
        retrieval["mrr"],
    )

    # Рефакторинг: Безопасная проверка, что в словаре generation есть метрики,
    # а не просто пустой объект или None (актуально для режима "retrieval")
    if generation and any(generation.values()):
        logger.info(
            "Faithfulness: %.3f",
            generation.get("faithfulness", 0.0),
        )

        logger.info(
            "Relevance: %.3f",
            generation.get("relevance", 0.0),
        )

        logger.info(
            "Correctness: %.3f",
            generation.get("correctness", 0.0),
        )


if __name__ == "__main__":
    asyncio.run(main())
