"""metrics константы"""

from prometheus_client import Counter, Histogram


SERVICE_NAME = "researcher"


RAG_REQUESTS_TOTAL = Counter(
    "rag_requests_total",
    "Total number of RAG requests",
    ["service"],
)


RAG_REQUEST_ERRORS_TOTAL = Counter(
    "rag_request_errors_total",
    "Total number of failed RAG requests",
    ["service"],
)


RAG_REQUEST_DURATION = Histogram(
    "rag_request_duration_seconds",
    "Total RAG request duration",
    ["service"],
)


RAG_QUERY_GENERATION_DURATION = Histogram(
    "rag_query_generation_duration_seconds",
    "Time spent generating search queries",
    ["service"],
)


RAG_GENERATED_QUERIES = Histogram(
    "rag_generated_queries",
    "Number of generated queries per RAG request",
    ["service"],
)


RAG_RETRIEVAL_DURATION = Histogram(
    "rag_retrieval_duration_seconds",
    "Time spent retrieving documents",
    ["service"],
)


RAG_RETRIEVED_DOCUMENTS = Histogram(
    "rag_retrieved_documents",
    "Number of documents retrieved per generated query",
    ["service"],
)


RAG_CONTEXT_DOCUMENTS = Histogram(
    "rag_context_documents",
    "Number of unique documents passed to the LLM",
    ["service"],
)


RAG_LLM_DURATION = Histogram(
    "rag_llm_duration_seconds",
    "Time spent generating final LLM response",
    ["service"],
)


# quality

RAG_TTFT = Histogram(
    "rag_llm_time_to_first_token_seconds",
    "Time from LLM generation start to first token",
    ["service"],
)

RAG_INTER_TOKEN_LATENCY = Histogram(
    "rag_llm_inter_token_latency_seconds",
    "Time between generated tokens",
    ["service"],
)

RAG_GENERATED_TOKENS = Histogram(
    "rag_llm_generated_tokens",
    "Number of generated tokens",
    ["service"],
)

RAG_TOKENS_PER_SECOND = Histogram(
    "rag_llm_tokens_per_second",
    "LLM generation throughput",
    ["service"],
)
