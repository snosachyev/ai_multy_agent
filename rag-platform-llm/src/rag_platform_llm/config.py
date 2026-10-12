"""LLMConfig config"""
from dataclasses import dataclass


@dataclass(frozen=True)
class LLMConfig:
    """LLMConfig"""
    provider: str
    model: str
    temperature: float = 0
    base_url: str | None = None
    api_key: str | None = None
