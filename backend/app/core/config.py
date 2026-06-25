from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    database_url: str
    database_url_sync: str

    redis_url: str = "redis://localhost:6379/0"

    groq_api_key: str

    serper_api_key: str = ""

    langchain_tracing_v2: bool = False
    langchain_api_key: str = ""
    langchain_project: str = "lead-research-agent"

    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    debug: bool = False

    celery_broker_url: str
    celery_result_backend: str

    default_min_score_threshold: int = Field(default=6, ge=1, le=10)
    default_email_tone: str = "conversational"
    default_email_angle: str = "pain"

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"
    
    @property
    def is_production(self) -> bool:
        return self.app_env == "production"
    
settings = Settings()

