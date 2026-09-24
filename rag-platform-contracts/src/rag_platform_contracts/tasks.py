from pydantic import BaseModel, Field


class AgentTaskRequest(BaseModel):
    # workflow_id: str
    # task_id: str
    user_input: str
    # task: str

    context: dict = Field(
        default_factory=dict
    )