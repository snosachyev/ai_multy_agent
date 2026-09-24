from pydantic import BaseModel


class WorkflowRunRequest(BaseModel):
    user_input: str
    max_iterations: int = 6


class WorkflowRunResponse(BaseModel):
    workflow_id: str
    user_input: str
    final_answer: str | None

    iteration: int
    errors: list[str]

    agent_results: list[dict]