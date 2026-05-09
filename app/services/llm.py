from langchain_openai import ChatOpenAI
from app.config import settings


def get_llm(provider: str, model: str, streaming: bool = False) -> ChatOpenAI:
    if provider == "groq":
        return ChatOpenAI(
            model=model,
            api_key=settings.groq_api_key,
            base_url="https://api.groq.com/openai/v1",
            streaming=streaming,
            temperature=0,
        )
    return ChatOpenAI(
        model=model,
        api_key=settings.openai_api_key,
        streaming=streaming,
        temperature=0,
    )
