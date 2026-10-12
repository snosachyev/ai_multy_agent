"""llm platform factory file"""
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI

from .config import LLMConfig


def create_llm(config: LLMConfig) -> BaseChatModel:
    """create llm function"""

    if config.provider == "ollama":
        return ChatOllama(
            base_url=config.base_url,
            model=config.model,
            temperature=config.temperature,
        )

    if config.provider == "openai":
        return ChatOpenAI(
            api_key=config.api_key,
            model=config.model,
            temperature=config.temperature,
        )

    raise ValueError(
        f"Unsupported LLM provider: {config.provider}"
    )
