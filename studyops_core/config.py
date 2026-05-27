from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env')

    database_url: str = 'sqlite:///./studyops.db'
    deeptutor_base_url: str = 'http://localhost:8001'
    deeptutor_cli_enabled: bool = True
    deeptutor_rag_retrieval_profile: str = 'hybrid'
    hermes_base_url: str = 'http://localhost:9000'
    router_base_url: str = 'http://localhost:20128/v1'
    ninerouter_url: str = 'http://localhost:20128'
    ninerouter_key: str | None = None
    ninerouter_default_chat_model: str = 'openai/gpt-4o-mini'


settings = Settings()
