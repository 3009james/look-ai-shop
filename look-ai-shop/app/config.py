from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "LOOK AI"
    bot_token: str = ""
    webapp_url: str = "http://localhost:8000"
    admin_telegram_id: int | None = None
    dev_mode: bool = True
    auth_max_age_seconds: int = 86400

    database_url: str = "sqlite:///./lookai.db"

    ai_base_url: str = ""
    ai_api_key: str = ""
    ai_model: str = ""
    ai_timeout_seconds: int = 30

    model_config = SettingsConfigDict(env_file=".env", extra="ignore", env_ignore_empty=True)


@lru_cache
def get_settings() -> Settings:
    return Settings()
