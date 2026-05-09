from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    openai_api_key: str = ""
    groq_api_key: str = ""
    tavily_api_key: str = ""

    llm_provider: str = "openai"
    llm_model: str = "gpt-4o-mini"


settings = Settings()
