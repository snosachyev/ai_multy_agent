from pydantic import BaseModel, Field


class FinalizationRequest(BaseModel):
    workflow_id: str
    user_input: str = Field(min_length=1, max_length=10_000)

    researcher_result: str | None = None
    analysis_result: str | None = None


class FinalizationResponse(BaseModel):
    workflow_id: str
    final_answer: str
    success: bool
    error: str | None = None