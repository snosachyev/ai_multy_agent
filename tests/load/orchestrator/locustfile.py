"""Модуль нагрузочного тестирования API Оркестратора.

Используется для проведения Smoke-тестов производительности в CI/CD
и регрессионного нагрузочного тестирования эндпоинтов развертывания.
В процессе теста симулируется высококонкурентная отправка запросов
на инициализацию и выполнение мультиагентных воркфлоу.
"""


import logging
from locust import HttpUser, between, events, task


# Настройка логирования, чтобы видеть сообщения в консоли GitHub Actions
logger = logging.getLogger(__name__)


# --- Конфигурация SLA ---
# Максимально допустимый 95-й перцентиль времени ответа в миллисекундах
MAX_P95_RESPONSE_TIME = 500


class OrchestratorUser(HttpUser):
    """Класс, симулирующий виртуального пользователя Оркестратора.

    Каждый пользователь выполняет задачи с цикличной задержкой
    между запросами от 0.1 до 0.5 секунды.
    """
    wait_time = between(0.1, 0.5)

    @task
    def run_workflow(self):
        """Тестирование эндпоинта запуска мультиагентного воркфлоу.

        Отправляет POST-запрос на `/api/v1/workflows/run` с тестовым промптом.
        Валидирует:
        - HTTP статус-код (ожидается 200).
        - Корректность структуры ответа (ожидается валидный JSON).
        - Наличие непустого тела ответа.

        При любых отклонениях от ожидаемого поведения фиксирует ошибку
        в отчете Locust, что приводит к падению CI при наличии
        флага --exit-code-on-error.
        """
        with self.client.post(
            "/api/v1/workflows/run",
            json={
                "user_input": "What is RAG?",
                "max_iterations": 3,
            },
            name="POST /api/v1/workflows/run",
            catch_response=True,
        ) as response:
            if response.status_code != 200:
                response.failure(
                    f"Unexpected status code: {response.status_code}"
                )
                return

            try:
                data = response.json()
            except ValueError:
                response.failure("Response is not valid JSON")
                return

            if not data:
                response.failure("Empty workflow response")


# --- Хук для проверки SLA после завершения теста ---
@events.quitting.connect
def check_sla(environment, **_kwargs):
    """Проверяет соответствие результатов теста заданным критериям SLA.

    Вызывается автоматически в момент завершения работы Locust.
    Если p95 время ответа превышает лимит, принудительно выставляет
    код выхода из процесса равным 1, что роняет джобу в CI.
    """
    # Если тест запускался в режиме headless (как в CI), проверяем метрики
    if environment.stats:
        # Получаем общую статистику для всех запросов
        aggregated_stats = environment.stats.total

        # Получаем аппроксимированный 95-й перцентиль времени ответа
        p95 = aggregated_stats.get_current_response_time_percentile(0.95)

        # Используем "ленивое" %-форматирование для логгера (исправление предупреждения)
        logger.info(
            "=== Проверка SLA: Текущий p95 = %dмс (Лимит: %dмс) ===",
            p95,
            MAX_P95_RESPONSE_TIME
        )

        if p95 > MAX_P95_RESPONSE_TIME:
            logger.error(
                "CRITICAL: SLA нарушен! p95 время ответа (%dмс) превысило лимит %dмс.",
                p95,
                MAX_P95_RESPONSE_TIME
            )
            # Меняем код выхода Locust. Это заставит runner в GitHub Actions выдать ошибку.
            environment.process_exit_code = 1
