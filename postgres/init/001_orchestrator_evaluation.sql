CREATE TABLE IF NOT EXISTS orchestrator_evaluation_runs (
    run_id UUID PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL,
    git_commit TEXT,
    dataset TEXT NOT NULL,
    mode TEXT NOT NULL,

    questions_count INTEGER NOT NULL,
    max_iterations INTEGER NOT NULL,

    task_completion DOUBLE PRECISION NOT NULL,
    workflow_completed DOUBLE PRECISION NOT NULL,
    routing_success DOUBLE PRECISION NOT NULL,
    agent_execution_success_rate DOUBLE PRECISION NOT NULL,

    avg_iterations DOUBLE PRECISION NOT NULL,
    avg_agent_calls DOUBLE PRECISION NOT NULL,
    avg_errors DOUBLE PRECISION NOT NULL,
    avg_duration_ms DOUBLE PRECISION NOT NULL,

    results JSONB NOT NULL
);