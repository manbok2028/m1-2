"""Environment-backed application settings. Secrets never live in source code."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"
    firebase_service_account_json: str | None = None
    firebase_service_account_file: str | None = None
    ecos_api_key: str | None = None
    # Keep the deployed Vercel client usable even before an optional
    # ALLOWED_ORIGINS override is supplied by the hosting dashboard.
    allowed_origins: str = (
        "http://localhost:5500,http://127.0.0.1:5500,"
        "https://m1-2.vercel.app"
    )
    ai_demo_mode: bool = True

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"

    @property
    def firebase_credentials(self) -> str | None:
        """Prefer the deployment JSON environment variable; allow a gitignored local file."""
        if self.firebase_service_account_json:
            return self.firebase_service_account_json
        if self.firebase_service_account_file:
            path = Path(self.firebase_service_account_file)
            if path.exists():
                return path.read_text(encoding="utf-8")
        return None


@lru_cache
def get_settings() -> Settings:
    return Settings()
