"""Environment-backed application settings. Secrets never live in source code."""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"
    firebase_service_account_json: str | None = None
    ecos_api_key: str | None = None
    allowed_origins: str = "http://localhost:5500,http://127.0.0.1:5500"
    ai_demo_mode: bool = True

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
