# cоздать network
    docker network create rag-network


# контракты
    cd rag-platform-contracts
    python -m build
    cp dist/*.whl packages/
    cd ../
    cp rag-platform-contracts/dist/*.whl packages/


# Запросы
## Оркестратор
    curl -X 'POST' \
    'http://127.0.0.1:8000/v1/workflows/run' \
    -H 'accept: application/json' \
    -H 'Content-Type: application/json' \
    -d '{
        "user_input": "Узнай в документах, что такое task decomposition для LLM агентов. После этого посчитай: если у нас есть задача, которую агент разбивает на 4 подзадачи, и на каждую подзадачу тратится по 3 вызова API, сколько всего вызовов API сделает система?",
        "max_iterations": 6
    }'

## Researcher
    curl -X 'POST' \
    'http://127.0.0.1:8002/api/v1/researcher/search' \
    -H 'accept: application/json' \
    -H 'Content-Type: application/json' \
    -d '{
        "workflow_id": "ea881a87-7519-46b1-8fdc-6f42ddb1c313",
        "task": "Ищите определение task decomposition для LLM агентов."
    }'

## Analyst
    curl -X 'POST'  \
        'http://127.0.0.1:8003/api/v1/analyst/analyze'     
        -H 'accept: */*'
        -H 'Content-Type: application/json'
        -d '{
            "context": {
            "workflow_id": "204801b2-0678-4e51-abed-5f4ad42217c4",
            "task": "Analyze the details of task decomposition methods for LLM agents.",
            "researcher_result": "Task decomposition для LLM агентов включает в себя разбиение сложной задачи на более мелкие и управляемые подзадачи, чтобы эффективно обрабатывать сложные задачи. Этот процесс может осуществляться несколькими способами:\n1. С помощью LLM с простым подсказыванием, например, \"Шаги для XYZ.\\n1.\", \"Какие подзадачи необходимо выполнить для достижения XYZ?\".\n2. С использованием специфических инструкций для задач; например, \"Напишите план рассказа\" для написания романа.\n3. С помощью человеческого ввода.\nВ дополнительном подходе LLM+P (Liu et al. 2023) планирование делегируется внешнему классическому планировщику через промежуточный интерфейсPlanning Domain Definition Language (PDDL)."
            }, "user_input": "Узнай в документах, что такое task decomposition для LLM агентов. После этого посчитай: если у нас есть задача, которую агент разбивает на 4 подзадачи, и на каждую подзадачу тратится по 3 вызова API, сколько всего вызовов API сделает система?"
        }
    '

## Director
    curl -X 'POST' \
    'http://0.0.0.0:8001/v1/decide' \
    -H 'accept: application/json' \
    -H 'Content-Type: application/json' \
    -d '{
        "user_input": "Узнай в документах, что такое task decomposition для LLM агентов. После этого посчитай: если у нас есть задача, которую агент разбивает на 4 подзадачи, и на каждую подзадачу тратится по 3 вызова API, сколько всего вызовов API сделает система?",
        "context": {
        "workflow_id": "0caa5270-205c-47c2-aa12-d09f2bbbb033",
        "iteration": 0,
        "max_iterations": 6,
        "research_result": null,
        "current_agent": null,
        "current_task": null,
        "analysis_result": null,
        "agent_results": [],
        "errors": [],
        "completed_tasks": null,
        "last_action": null,
        "final_answer": null,
        "last_agent_success": null,
        "last_error": null
        }
    }
    '
    
# проверить метрики в базе
    docker exec -it ai_agetn_laggraph-postgres-1 psql -U rag -d rag_evaluation
    \dt
    \d evaluation_runs
    SELECT * FROM evaluation_runs;


# tests
    export RAG_SPLITS_PATH="$(pwd)/data/rag-platform-researcher/data/my_splits.pkl"

## orcetration
    export DIRECTOR_SERVICE_URL="http://0.0.0.0:8001"
    export RESEARCHER_SERVICE_URL="http://0.0.0.0:8002"
    export ANALYST_SERVICE_URL="http://0.0.0.0:8003"
    export FINALIZER_SERVICE_URL="http://0.0.0.0:8004"
    .venv/bin/python -m pytest tests/e2e/orchestrator/ -v

# load test
    locust \
  -f tests/load/orchestrator/locustfile.py \
  --host http://localhost:8000
## запуск нагрузочного теста с фейк сервисами
    docker compose -f docker-compose.yml -f docker-compose.load-test.yml up -d orchestrator fake-agents
    locust \
  -f tests/load/orchestrator/locustfile.py \
  --host http://localhost:8000


# build base docker
    docker build  --no-cache  -f docker/transformer-base.Dockerfile   -t transformer-base:latest   .
    docker build  --no-cache -f docker/rag-python-base.Dockerfile   -t rag-python-base:latest   .

# evaluation
## orchestrator
    python -m evaluation.orchestrator.run_evaluation --mode smoke --no-db
    ./evaluation/run_orchestrator_evaluate.sh 

## researcher
    ./evaluation/run_researcher_evaluate.sh


# postgress evaluation
    docker compose exec postgres psql -U rag -d rag_evaluation

# условие запуска CI
    git add .
    git commit -m "ci: add github actions pipeline"
    git push