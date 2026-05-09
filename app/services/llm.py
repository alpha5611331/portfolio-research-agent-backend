from langchain_anthropic import ChatAnthropic
from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI

from app.config import settings

_BASE_URLS: dict[str, str] = {
    "openai": "https://api.openai.com/v1",
    "groq": "https://api.groq.com/openai/v1",
}

_API_KEYS: dict[str, str] = {
    "openai": settings.openai_api_key,
    "groq": settings.groq_api_key,
    "anthropic": settings.anthropic_api_key,
}


def get_llm(streaming: bool = False) -> BaseChatModel:
    provider = settings.llm_provider
    model = settings.llm_model
    api_key = _API_KEYS.get(provider, "")

    if provider == "anthropic":
        return ChatAnthropic(
            model=model,
            api_key=api_key,
            streaming=streaming,
        )

    base_url = _BASE_URLS.get(provider, "https://api.openai.com/v1")
    return ChatOpenAI(
        model=model,
        api_key=api_key,
        base_url=base_url,
        streaming=streaming,
        temperature=0,
    )
