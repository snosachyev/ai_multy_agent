from pydantic import BaseModel, Field


class AgentTaskRequest(BaseModel):
    user_input: str
    context: dict = Field(
        default_factory=dict
    )
