"""
End-to-End (E2E) tests for the Researcher service API component.

This module validates the complete integration flow of the Researcher component
by sending real HTTP requests to a fully operational deployment. It verifies
the end-to-end execution path, including routing, model inference, and external
data store retrieval.

Requirements:
    - Running Researcher service instance.
    - Configured and accessible LLM/retrieval infrastructure.

Environment Variables:
    RESEARCHER_SERVICE_URL: Base target URL (defaults to http://localhost:8001).
    RESEARCHER_TIMEOUT: Maximum wait time for network operations.
"""
import os

import pytest
from httpx import AsyncClient

from tests.config.settings import get_researcher_timeout


@pytest.mark.e2e
@pytest.mark.anyio
async def test_researcher_e2e():
    """
    Verify the complete Researcher API workflow against a running service.

    Sends a research task to the real Researcher service and validates:
    - HTTP response status;
    - workflow identification;
    - successful execution;
    - generated answer;
    - retrieved documents;
    - generated search queries.

    The test expects the Researcher service and its dependencies,
    including the LLM and retrieval infrastructure, to be available.

    Environment variables:
        RESEARCHER_SERVICE_URL: Base URL of the Researcher service.
        RESEARCHER_TIMEOUT: Maximum response wait time in seconds.
    """
    base_url = os.getenv(
        "RESEARCHER_SERVICE_URL",
        "http://localhost:8001",
    )

    workflow_id = "ea881a87-7519-46b1-8fdc-6f42ddb1c313"
    task = "Что такое RAG?"

    async with AsyncClient(
        base_url=base_url,
        timeout=get_researcher_timeout(),
    ) as client:
        response = await client.post(
            "/api/v1/researcher/search",
            json={
                "workflow_id": workflow_id,
                "task": task,
            },
        )

    assert response.status_code == 200, (
        f"Unexpected status code: {response.status_code}. "
        f"Response: {response.text}"
    )

    data = response.json()

    assert data["success"] is True
    assert data["workflow_id"] == workflow_id

    result = data["result"]

    assert result["question"] == task
    assert result["answer"]
    assert result["documents"]
    assert result["generated_queries"]

    assert isinstance(result["documents"], list)
    assert isinstance(result["generated_queries"], list)
