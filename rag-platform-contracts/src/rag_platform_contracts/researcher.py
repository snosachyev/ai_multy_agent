from pydantic import BaseModel, Field


class ResearchRequest(BaseModel):
    workflow_id: str
    task: str = Field(min_length=1, max_length=10_000)


class RetrievedDocument(BaseModel):
    id: str
    content: str
    metadata: dict
    matched_queries: list[int] = []


class RAGResult(BaseModel):
    question: str
    generated_queries: list[str]
    documents: list[RetrievedDocument]
    context: str
    answer: str


class ResearchResponse(BaseModel):
    workflow_id: str
    result: RAGResult
    success: bool
    error: str | None = None