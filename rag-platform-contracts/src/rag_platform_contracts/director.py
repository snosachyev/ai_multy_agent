from pydantic import BaseModel, Field
from typing import Literal

from rag_platform_contracts.agents import NextAction


class DirectorDecision(BaseModel):
    next_action: Literal[
        "researcher",
        "analyst",
        "finish"
    ] = Field(
        description="Следующий шаг системы"
    )

    reason: str = Field(
        description="Краткое объяснение выбора"
    )

    task: str = Field(
        description=(
            "Конкретная задача для выбранного агента. "
            "Если next_action='finish', можно указать "
            "причину завершения."
        )
    )
