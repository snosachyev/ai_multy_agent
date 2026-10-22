"""Graph workflow module"""
from uuid import uuid4
import httpx
from langgraph.graph import (
    END,
    START,
    StateGraph,
)

from rag_platform_orchestrator.config.settings import settings

from rag_platform_orchestrator.domain.state import (
    AgentState,
)

from rag_platform_orchestrator.infrastructure.clients.director import (
    DirectorClient,
)

from rag_platform_orchestrator.infrastructure.clients.researcher import (
    ResearcherClient,
)

from rag_platform_orchestrator.infrastructure.clients.analyst import (
    AnalystClient,
)

from rag_platform_orchestrator.infrastructure.clients.finalizer import (
    FinalizerClient,
)

from rag_platform_contracts.agents import (
    NextAction,
)

from rag_platform_observability.observability import get_logger


logger = get_logger(__name__)


class Workflow:
    """Graph workflow class"""
    def __init__(
        self,
        director: DirectorClient,
        researcher: ResearcherClient,
        analyst: AnalystClient,
        finalizer: FinalizerClient,
    ):
        """Graph workflow init"""
        self.director = director
        self.researcher = researcher
        self.analyst = analyst
        self.finalizer = finalizer

        self.graph = self._build_graph()

    def _build_graph(self):

        builder = StateGraph(AgentState)

        # ------------------------------------------------------------
        # Nodes
        # ------------------------------------------------------------

        builder.add_node(
            "director",
            self.director_node
        )

        builder.add_node(
            "researcher",
            self.researcher_node
        )

        builder.add_node(
            "analyst",
            self.analyst_node
        )

        builder.add_node(
            "finish",
            self.final_node
        )

        # =====================================================
        # START
        # =====================================================

        builder.add_edge(
            START,
            "director",
        )

        # =====================================================
        # DIRECTOR → AGENT
        # =====================================================

        builder.add_conditional_edges(
            "director",
            self.route_from_director,
            {
                "researcher": "researcher",
                "analyst": "analyst",
                "finish": "finish",
            },
        )

        # =====================================================
        # AGENT → DIRECTOR
        # =====================================================

        builder.add_conditional_edges(
            "researcher", 
            self.route_after_agent,
            {
                "director": "director", 
                "finish": "finish"
            }
        )

        builder.add_conditional_edges(
            "analyst",
            self.route_after_agent,
            {
                "director": "director",
                "finish": "finish",
            },
        )

        # =====================================================
        # FINISH → END
        # =====================================================

        builder.add_edge(
            "finish",
            END,
        )



        return builder.compile()


    async def director_node(
        self,
        state: AgentState,
    ):
        """director_node"""
        decision = await self.director.decide(
            workflow_id=state["workflow_id"],
            user_input=state["user_input"],
            iteration=state["iteration"],
            max_iterations=state["max_iterations"],
            current_agent=state["current_agent"],
            current_task=state["current_task"],
            research_result=state["research_result"],
            analysis_result=state["analysis_result"],
            agent_results=state["agent_results"],
            errors=state["errors"],
            final_answer=state["final_answer"],
            completed_tasks=state["completed_tasks"],
            last_action=state["last_action"],
            last_agent_success=state["last_agent_success"],
            last_error=state["last_error"],
        )
        return {
            "next_action": decision.next_action,
            "current_task": decision.task,
        }


    async def researcher_node(self, state: AgentState):
        """Высокоуровневый узел: координация шага исследователя."""
        # Передаем "чистый" стейт, клиент сам разберется с фолбеками строк
        current_task = state["current_task"]

        try:
            result = await self.researcher.execute(
                workflow_id=state["workflow_id"],
                user_input=state["user_input"],
                task=current_task,
            )

            if settings.debug_rag:
                logger.debug(f"[RESEARCHER RESULT], success={result.success}")

            if not result.result.get('success'):
                raise RuntimeError(result.error or "Researcher failed")

            agent_result = {
                "agent": "researcher",
                "task": result.task,  # Берем точный таск, зафиксированный клиентом
                "result": result.result,
                "success": True,
                "error": None,
            }

            return {
                "research_result": result.result['result']['answer'],
                "agent_results": [*state["agent_results"], agent_result],
                "next_action": state['next_action'],
                "last_action": "researcher",
                "last_agent_success": True,
                "last_error": None,
                "iteration": state["iteration"] + 1,
            }

        except (httpx.HTTPStatusError, httpx.NetworkError, httpx.TimeoutException) as net_exc:
            error_msg = f"Network error calling researcher: {type(net_exc).__name__}"
            logger.error(f"[RESEARCHER NODE] {error_msg}", exc_info=True)
            fallback_task = current_task or state["user_input"]
            return self._handle_node_error(state, fallback_task, error_msg, "researcher")

        except RuntimeError as biz_exc:
            error_msg = str(biz_exc)
            logger.warning(f"[RESEARCHER NODE] Business failure: {error_msg}")
            fallback_task = current_task or state["user_input"]
            return self._handle_node_error(state, fallback_task, error_msg, "researcher")

    async def analyst_node(
        self,
        state: AgentState,
    ):
        """analyst_node"""
        current_task = state["current_task"]

        try:
            result = await self.analyst.execute(
                user_input=state["user_input"],
                workflow_id=state["workflow_id"],
                task=state["current_task"],
                research_result=state["research_result"],
            )

            if not result.success:
                raise RuntimeError(
                    result.error or "Analyst failed"
                )

            agent_result = {
                "agent": "analyst",
                "task": state["current_task"],
                "result": result.result,
                "success": True,
                "error": None,
            }
            result_agent =  {
                "analysis_result": result.result['result'],

                "agent_results": [
                    *state["agent_results"],
                    agent_result,
                ],

                "last_action": "analyst",
                "last_agent_success": True,
                "last_error": None,

                "iteration": state["iteration"] + 1,
            }
            return result_agent

        except (httpx.HTTPStatusError, httpx.NetworkError, httpx.TimeoutException) as net_exc:
            error_msg = f"Network error calling researcher: {type(net_exc).__name__}"
            logger.error(f"[RESEARCHER NODE] {error_msg}", exc_info=True)
            fallback_task = current_task or state["user_input"]
            return self._handle_node_error(state, fallback_task, error_msg, "analyst")

        except RuntimeError as biz_exc:
            error_msg = str(biz_exc)
            logger.warning(f"[RESEARCHER NODE] Business failure: {error_msg}")
            fallback_task = current_task or state["user_input"]
            return self._handle_node_error(state, fallback_task, error_msg, "analyst")


    async def final_node(
        self,
        state: AgentState,
    ):
        """final_node"""
        result = await self.finalizer.execute(
            workflow_id=state["workflow_id"],
            user_input=state["user_input"],
            research_result=state[
                "research_result"
            ],
            analysis_result=state[
                "analysis_result"
            ]
        )

        return {
            "final_answer": result,
        }

    @staticmethod
    def route_after_agent(state: AgentState):
        """route_after_agent"""
        if state["last_agent_success"] is False:
            if settings.debug_rag:
                logger.debug("[ROUTER] Agent failed. Finishing workflow.")
                logger.debug("[ROUTER] Error: {state['last_error']}")
            return "finish"

        return "director"

    @staticmethod
    def route_from_director(state: AgentState):
        """route_from_director"""
        if state["iteration"] >= state["max_iterations"]:
            if settings.debug_rag:
                logger.debug("[ROUTER] Maximum iterations reached.")
            return "finish"

        action = state["next_action"]

        if action == "researcher":
            return "researcher"

        if action == "analyst":
            return "analyst"

        return "finish"

    async def run(
        self,
        user_input: str,
        max_iterations: int,
    ):
        """run graph method"""
        workflow_id = str(uuid4())

        initial_state: AgentState = {
            "workflow_id": workflow_id,

            "user_input": user_input,

            "current_agent": None,

            "current_task": None,

            "next_action":
                NextAction.RESEARCHER,

            "iteration": 0,

            "max_iterations":
                max_iterations,

            "research_result": None,

            "analysis_result": None,

            "agent_results": [],

            # Задачи, которые уже были успешно выполнены
            "completed_tasks": None,

            # --------------------------------------------------------
            # Последнее действие
            # --------------------------------------------------------

            "last_action": None,

            "last_agent_success": None,

            "last_error": None,

            "errors": [],

            "final_answer": None,
        }

        result = await self.graph.ainvoke(initial_state)

        return result


    # =====================================================================
    # ДЕТАЛИ РЕАЛИЗАЦИИ (Вспомогательные методы опущены в самый низ класса)
    # =====================================================================

    def _handle_node_error(
            self, state: AgentState, task: str, error_msg: str, agent_name: str
        ) -> dict:
        """Универсальный приватный хелпер сборки стейта ошибки для всех узлов графа."""
        return {
            "errors": [*state["errors"], error_msg],
            "agent_results": [
                *state["agent_results"],
                {
                    "agent": agent_name,
                    "task": task,
                    "result": "",
                    "success": False,
                    "error": error_msg,
                },
            ],
            "last_action": agent_name,
            "last_agent_success": False,
            "last_error": error_msg,
            "iteration": state["iteration"] + 1,
        }
