from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env')

    database_url: str = 'sqlite:///./studyops.db'
    deeptutor_base_url: str = 'http://localhost:8001'
    hermes_base_url: str = 'http://localhost:9000'
    router_base_url: str = 'http://localhost:20128/v1'


settings = Settings()
