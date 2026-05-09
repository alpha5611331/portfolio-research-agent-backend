from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    openai_api_key: str = ""
    groq_api_key: str = ""
    tavily_api_key: str = ""
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "research_sessions"
    embedding_model: str = "text-embedding-3-small"
    default_provider: str = "openai"
    default_model: str = "gpt-4o-mini"


settings = Settings()
