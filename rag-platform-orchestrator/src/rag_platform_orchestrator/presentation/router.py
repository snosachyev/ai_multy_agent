"""Энтрипони оркестратора"""
from fastapi import APIRouter, Depends

from rag_platform_orchestrator.application.workflow import (
    Workflow,
)

from rag_platform_orchestrator.presentation.dependencies import (
    get_workflow_graph
)


from rag_platform_contracts.workflows import (
    WorkflowRunRequest,
)


router = APIRouter()

@router.post("/run")
async def run_workflow(
    request: WorkflowRunRequest,
    workflow: Workflow = Depends(get_workflow_graph),
):
    """Эндпоинт оркестратора, работающий с изолированным стейтом графа."""
    return await workflow.run(
        user_input=request.user_input,
        max_iterations=request.max_iterations,
    )
