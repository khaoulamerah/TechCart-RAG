
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ─── Ollama / Embedding (Étape 3) ──────────────────
    ollama_base_url: str = "http://localhost:11434"
    embedding_model: str = "nomic-embed-text"
    embedding_batch_size: int = 16
    embedding_timeout_seconds: float = 60.0
    embedding_max_retries: int = 3

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="TECHCART_",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()