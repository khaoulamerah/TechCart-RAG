from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ── App ──────────────────────────────────────
    PROJECT_NAME: str = "TechCart"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000

    # ── MongoDB ──────────────────────────────────
    MONGODB_URL: str
    MONGODB_DB: str = "techcart"

    # ── Qdrant ───────────────────────────────────
    QDRANT_HOST: str = "qdrant"
    QDRANT_PORT: int = 6333
    QDRANT_GRPC_PORT: int = 6334
    QDRANT_COLLECTION: str = "techcart_products"

    # ── Ollama ───────────────────────────────────
    OLLAMA_BASE_URL: str = "http://host.docker.internal:11434"
    LLM_MODEL: str = "mistral:latest"
    EMBEDDING_MODEL: str = "BAAI/bge-m3"

    # ── RAG settings ─────────────────────────────
    CHUNK_SIZE: int = 512
    CHUNK_OVERLAP: int = 100
    TOP_K_RESULTS: int = 5
    SIMILARITY_THRESHOLD: float = 0.7

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()