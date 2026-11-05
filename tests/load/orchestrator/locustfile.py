"""Модуль нагрузочного тестирования API Оркестратора.

Используется для проведения Smoke-тестов производительности в CI/CD
и регрессионного нагрузочного тестирования эндпоинтов развертывания.
В процессе теста симулируется высококонкурентная отправка запросов
на инициализацию и выполнение мультиагентных воркфлоу.
"""


from locust import HttpUser, between, task


class OrchestratorUser(HttpUser):
    """Класс, симулирующий виртуального пользователя Оркестратора.

    Каждый пользователь выполняет задачи с цикличной задержкой
    между запросами от 0.1 до 0.5 секунды.
    """
    wait_time = between(0.1, 0.5)

    @task
    def run_workflow(self):
        """Тестирование эндпоинта запуска мультиагентного воркфлоу.

        Отправляет POST-запрос на `/v1/workflows/run` с тестовым промптом.
        Валидирует:
        - HTTP статус-код (ожидается 200).
        - Корректность структуры ответа (ожидается валидный JSON).
        - Наличие непустого тела ответа.

        При любых отклонениях от ожидаемого поведения фиксирует ошибку
        в отчете Locust, что приводит к падению CI при наличии
        флага --exit-code-on-error.
        """
        with self.client.post(
            "/v1/workflows/run",
            json={
                "user_input": "What is RAG?",
                "max_iterations": 3,
            },
            name="POST /v1/workflows/run",
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
