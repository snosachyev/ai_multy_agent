CREATE TABLE researcher_evaluation_runs (
    run_id UUID PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL,
    git_commit TEXT,
    dataset TEXT NOT NULL,
    mode TEXT NOT NULL,
    
    -- Параметры конфигурации RAG
    embedding_model TEXT NOT NULL,
    llm_model TEXT NOT NULL,
    chunk_size INTEGER NOT NULL,
    chunk_overlap INTEGER NOT NULL,
    top_k INTEGER NOT NULL,
    questions_count INTEGER NOT NULL,
    
    -- Метрики оценки RAG
    recall_at_5 DOUBLE PRECISION,
    precision_at_5 DOUBLE PRECISION,
    mrr DOUBLE PRECISION,
    faithfulness DOUBLE PRECISION,
    relevance DOUBLE PRECISION,
    correctness DOUBLE PRECISION
);
