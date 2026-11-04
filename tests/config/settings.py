import os

import httpx


def get_researcher_timeout() -> httpx.Timeout:
    """Build HTTP timeout configuration for Researcher tests."""

    read_timeout = float(
        os.getenv("RESEARCHER_TIMEOUT", "300")
    )

    return httpx.Timeout(
        connect=10.0,
        read=read_timeout,
        write=30.0,
        pool=10.0,
    )