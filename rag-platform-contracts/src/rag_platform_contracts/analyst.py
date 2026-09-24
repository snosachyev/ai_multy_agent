from pydantic import BaseModel, Field


class AnalysisRequest(BaseModel):
    workflow_id: str
    task: str = Field(min_length=1, max_length=10_000)
    researcher_result: str | None = None


class AnalysisResponse(BaseModel):
    workflow_id: str
    result: str
    success: bool
    error: str | None = None