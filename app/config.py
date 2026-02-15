"""Application configuration using pydantic-settings."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables / .env file."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Azure OpenAI
    azure_openai_endpoint: str = ""
    azure_openai_deployment: str = "gpt-4o"
    azure_openai_api_version: str = "2024-12-01-preview"
    azure_openai_api_key: str | None = None

    # Azure AI Foundry Project (optional)
    azure_ai_project_connection_string: str | None = None

    # App
    app_env: str = "development"
    log_level: str = "INFO"

    @property
    def is_dev(self) -> bool:
        return self.app_env == "development"

    @property
    def use_key_auth(self) -> bool:
        return self.azure_openai_api_key is not None


@lru_cache
def get_settings() -> Settings:
    return Settings()
