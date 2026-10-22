"""Director client"""
from rag_platform_orchestrator.infrastructure.http import (
    ServiceClient,
)

from rag_platform_contracts.director import (
    DirectorDecision,
    DirectorRequest
)


class DirectorClient(ServiceClient):
    """DirectorClient класс"""
    async def decide(
        self,
        *,
        workflow_id: str,
        user_input: str,
        iteration: int,
        max_iterations: int,
        research_result: str | None,
        current_agent: str | None,
        current_task: str | None,
        analysis_result: str | None,
        agent_results: list[dict],
        errors: list[str],
        final_answer: str | None,
        completed_tasks: str | None,
        last_action: str | None,
        last_agent_success: str | None,
        last_error: str | None,
    ) -> DirectorDecision:
        """Class director client"""
        request = DirectorRequest(
            # workflow_id=workflow_id,
            # task_id=f"{workflow_id}-director-{iteration}",
            user_input=user_input,
            # task="Определи следующий шаг workflow.",
            context={
                "workflow_id": workflow_id,
                "iteration": iteration,
                "max_iterations": max_iterations,
                "research_result": research_result,
                "current_agent": current_agent,
                "current_task": current_task,
                "analysis_result": analysis_result,
                "agent_results": agent_results,
                "errors": errors,
                'completed_tasks': completed_tasks,
                'last_action': last_action,
                'final_answer': final_answer,
                'last_agent_success': last_agent_success,
                'last_error': last_error,
            },
        )
        response = await self.client.post(
            f"{self.base_url}/api/v1/director/decide",
            json=request.model_dump(),
        )

        response.raise_for_status()

        return DirectorDecision.model_validate(
            response.json()
        )
