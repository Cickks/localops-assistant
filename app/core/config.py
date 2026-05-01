"""
Application configuration.

Loads environment variables from .env into a validated, typed Pydantic Settings object.
This is the only place in the codebase that reads environment variables directly.
All other modules import the `settings` instance from here.
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings, loaded from environment variables and/or .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = Field(default="aisteve", description="Application name used in logs.")
    app_env: Literal["development", "staging", "production"] = Field(
        default="development",
        description="Runtime environment. Affects log format and error verbosity.",
    )
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Minimum log level to emit.",
    )

    # Server
    host: str = Field(default="0.0.0.0", description="Network interface to bind.")
    port: int = Field(default=8000, ge=1, le=65535, description="TCP port to listen on.")

    # Ollama
    ollama_base_url: str = Field(
        default="http://localhost:11434",
        description="Base URL of the Ollama HTTP API.",
    )
    ollama_default_model: str = Field(
        default="llama3.1:8b",
        description="Default model name when not specified in a request.",
    )
    ollama_timeout_seconds: float = Field(
        default=120.0,
        gt=0,
        description="HTTP request timeout when calling Ollama.",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Return a cached Settings instance.

    Using lru_cache means we only parse the environment once per process,
    even if get_settings() is called from many places. This also makes it
    easy to override in tests by clearing the cache.
    """
    return Settings()


# Module-level convenience: most code imports `settings` directly.
settings = get_settings()
