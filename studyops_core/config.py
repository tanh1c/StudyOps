from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = 'sqlite:///./studyops.db'
    deeptutor_base_url: str = 'http://localhost:8001'
    hermes_base_url: str = 'http://localhost:9000'
    router_base_url: str = 'http://localhost:20128/v1'

    class Config:
        env_file = '.env'


settings = Settings()
