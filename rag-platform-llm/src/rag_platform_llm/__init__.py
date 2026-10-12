"""llm platform entry point"""
from .config import LLMConfig
from .factory import create_llm

__all__ = [
    "LLMConfig",
    "create_llm",
]
