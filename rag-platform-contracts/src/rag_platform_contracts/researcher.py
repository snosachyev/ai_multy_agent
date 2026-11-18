"""Pydantic-схемы запросов и ответов для RAG-пайплайна исследований."""

from pydantic import BaseModel, Field


class ResearchRequest(BaseModel):
    """Запрос на запуск исследовательского пайплайна.

    Attributes:
        workflow_id: Уникальный идентификатор рабочего процесса.
        task: Текст исследовательской задачи или вопроса.
        source_ids: Список ID источников для фильтрации поиска
            (если None — поиск по всем доступным источникам).
    """

    workflow_id: str
    task: str = Field(min_length=1, max_length=10_000)
    source_ids: list[str] | None = Field(
        default=None,
        description="Список ID источников для фильтрации поиска (если None — поиск по всем)",
    )


class RetrievedDocument(BaseModel):
    """Документ или фрагмент текста, найденный в процессе поиска.

    Attributes:
        id: Уникальный идентификатор документа.
        content: Текстовое содержимое документа.
        metadata: Словарь с дополнительными метаданными документа.
        matched_queries: Список индексов сгенерированных запросов,
            по которым был найден данный документ.
    """

    id: str
    content: str
    metadata: dict
    matched_queries: list[int] = []


class RAGResult(BaseModel):
    """Результат работы RAG-пайплайна (Retrieval-Augmented Generation).

    Attributes:
        question: Исходный вопрос пользователя.
        generated_queries: Список поисковых запросов, сформированных на основе вопроса.
        documents: Список релевантных документов, отобранных при поиске.
        context: Итоговый текстовый контекст, собранный из найденных документов.
        answer: Сгенерированный ответ на основе собранного контекста.
    """

    question: str
    generated_queries: list[str]
    documents: list[RetrievedDocument]
    context: str
    answer: str


class ResearchResponse(BaseModel):
    """Ответ на запрос выполнения исследовательского пайплайна.

    Attributes:
        workflow_id: Уникальный идентификатор рабочего процесса.
        result: Детальные результаты работы RAG-пайплайна.
        success: Флаг успешного завершения операции.
        error: Сообщение об ошибке, если выполнение завершилось неудачно.
    """

    workflow_id: str
    result: RAGResult
    success: bool
    error: str | None = None


class SourcesResponse(BaseModel):
    """Ответ со списком доступных источников данных.

    Attributes:
        sources: Список идентификаторов или названий доступных источников.
    """

    sources: list[str]
