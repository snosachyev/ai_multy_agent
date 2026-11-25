"""Схемы запросов и ответов для запуска и отслеживания рабочих процессов (workflows)."""

from pydantic import BaseModel, Field


class WorkflowRunRequest(BaseModel):
    """Запрос на запуск рабочего процесса (workflow).

    Attributes:
        user_input: Входной текстовый запрос пользователя.
        max_iterations: Максимальное количество итераций выполнения процесса.
        source_ids: Список ID источников для фильтрации поиска.
            Если None — поиск выполняется по всем доступным источникам.
    """

    user_input: str
    max_iterations: int = 6
    source_ids: list[str] | None = Field(
        default=None,
        description="Список ID источников для фильтрации поиска (если None — поиск по всем)",
    )


class WorkflowRunResponse(BaseModel):
    """Результат выполнения рабочего процесса (workflow).

    Attributes:
        workflow_id: Уникальный идентификатор запущенного рабочего процесса.
        user_input: Исходный текстовый запрос пользователя.
        final_answer: Итоговый ответ системы. Может быть None, если ответ не сформирован.
        iteration: Количество фактически выполненных итераций.
        errors: Список сообщений об ошибках, возникших в процессе выполнения.
        agent_results: Промежуточные или детальные результаты работы отдельных агентов.
    """

    workflow_id: str
    user_input: str
    final_answer: str | None
    iteration: int
    errors: list[str]
    agent_results: list[dict]
