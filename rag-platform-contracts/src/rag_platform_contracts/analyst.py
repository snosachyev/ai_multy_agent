from pydantic import BaseModel, Field


class AnalysisRequest(BaseModel):
    user_input: str
    context: dict = Field(
        default_factory=dict
    )


class AnalysisResponse(BaseModel):
    workflow_id: str
    result: str
    success: bool
    error: str | None = None