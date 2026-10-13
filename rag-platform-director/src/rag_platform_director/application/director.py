"""Director RAG service"""
from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from rag_platform_contracts.director import DirectorDecision, DirectorRequest


class DirectorService:
    """Director RAG service"""

    def __init__(self, llm: BaseChatModel) -> None:
        """Инициализирует сервис аналитики с заданной языковой моделью.

        Args:
            llm: Экземпляр чат-модели LangChain, поддерживающий структурированный вывод.
        """
        self.llm = llm
        self.chain = self._build_prompt() | self.llm.with_structured_output(
            DirectorDecision
        )

    @staticmethod
    def _build_prompt():

        return ChatPromptTemplate.from_messages([
            (
                "system",
                """
                Ты — Главный Директор мультиагентной системы.
                
                Ты управляешь двумя специалистами.
                
                RESEARCHER:
                Ищет информацию в закрытых документах через RAG.
                
                ANALYST:
                Выполняет математические расчёты, анализирует код
                и решает логические задачи.
                
                Твоя задача — определить СЛЕДУЮЩИЙ шаг workflow.
                
                ============================================================
                ПРАВИЛА
                ============================================================
                
                1. Если нужна информация из документов → researcher.
                
                2. Если нужно выполнить расчёт, анализ кода
                или логическую операцию → analyst.
                
                3. Если задача полностью решена → finish.
                
                4. Не вызывай агента повторно без причины.
                
                5. Если researcher уже дал необходимую информацию,
                передай её analyst.
                
                6. Если analyst уже выполнил необходимый расчёт,
                дополнительных действий обычно не требуется → finish.
                
                7. Учитывай ВСЮ историю выполнения.
                
                8. Учитывай completed_tasks.
                
                9. Если задача уже успешно выполнена,
                НЕ назначай её повторно.
                
                10. Если последний агент завершился с ошибкой,
                    НЕ вызывай тот же агент повторно автоматически,
                    если причина ошибки является программной,
                    инфраструктурной или связана с отсутствующим инструментом.
                
                11. Например, если появилась ошибка:
                
                    "name 'run_rag_search' is not defined"
                
                    нельзя снова отправлять researcher,
                    потому что researcher не способен исправить
                    Python-код оркестратора.
                
                12. Если выполнение невозможно продолжить,
                    выбери finish.
                
                13. Никогда не создавай цикл:
                
                    researcher → researcher → researcher
                
                    или
                
                    analyst → analyst → analyst
                
                    без новой причины.
                
                14. Не выполняй работу researcher или analyst сам.
                    Ты только принимаешь решение.
                
                15. Если выбираешь researcher или analyst,
                    task должен содержать КОНКРЕТНУЮ задачу агенту.
                
                16. Если выбираешь finish,
                    task должен кратко описывать причину завершения.
                
                ============================================================
                ЗАЩИТА ОТ ЦИКЛОВ
                ============================================================
                
                Если iteration близка к max_iterations,
                старайся завершить workflow.
                
                Если уже была выполнена необходимая работа,
                не назначай её повторно.
                
                Если предыдущая попытка завершилась ошибкой
                и повторение не изменит ситуацию,
                выбирай finish.
                """
            ),

            (
                "human",
                """
                Исходная задача пользователя:
                
                {user_input}
                
                
                Текущая итерация:
                
                {iteration} из {max_iterations}
                
                
                Текущий агент:
                
                {current_agent}
                
                
                Текущая задача:
                
                {current_task}
                
                
                Результат Researcher:
                
                {research_result}
                
                
                Результат Analyst:
                
                {analysis_result}
                
                
                История выполнения:
                
                {agent_results}
                
                
                Успешно выполненные задачи:
                
                {completed_tasks}
                
                
                Последнее действие:
                
                {last_action}
                
                
                Успешность последнего агента:
                
                {last_agent_success}
                
                
                Последняя ошибка:
                
                {last_error}
                
                
                Ошибки:
                
                {errors}
                
                
                Определи следующий шаг.
                """
            ),
        ])

    async def decide( self, request: DirectorRequest) -> DirectorDecision:
        """Запускает цепочку решения на основе входящего запроса.
            Args:
                request: Объект контракта DirectorRequest с входными данными и контекстом.
        
            Returns:
                DirectorDecision: Валидированный структурированный ответ от LLM.
        """

        # Теперь мы легко собираем state из context и user_input
        context = request.context
        chain_result: DirectorDecision = await self.chain.ainvoke({
            "user_input": request.user_input,
            "iteration": context.get("iteration", 0),
            "max_iterations": context.get("max_iterations", 6),
            "current_agent": context.get("current_agent") or "Нет",
            "current_task": context.get("current_task") or "Нет", # Заменили на актуальное поле
            "research_result": context.get("research_result") or "Нет данных",
            "analysis_result": context.get("analysis_result") or "Нет данных",
            "agent_results": context.get("agent_results") or [],
            # Новые поля из роута автоматически доступны здесь через context.get():
            "workflow_id": context.get("workflow_id"),
            "errors": context.get("errors", []),
            "completed_tasks": context.get("completed_tasks"),
            "last_action": context.get("last_action"),
            "final_answer": context.get("final_answer"),
            "last_agent_success": context.get("last_agent_success"),
            "last_error": context.get("last_error"),
        })

        return chain_result
