from pydantic import BaseModel
from typing import Any


class AgentExecutionResponse(BaseModel):
    agent: str
    task: str
    result: str | dict[str, Any]  # Теперь Pydantic пропустит и строку, и словарь
    success: bool
    error: str | None = None
