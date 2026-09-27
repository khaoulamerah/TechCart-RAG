from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ── Application ──────────────────────────────────────────
    PROJECT_NAME: str = "TechCart"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000

    # ── MongoDB ──────────────────────────────────────────────
    MONGODB_URL: str
    MONGODB_DB: str = "techcart"

    # ── Qdrant ───────────────────────────────────────────────
    QDRANT_HOST: str = "qdrant"
    QDRANT_PORT: int = 6333
    QDRANT_GRPC_PORT: int = 6334

    # Selected embedding model collection
    QDRANT_COLLECTION: str = "techcart_bge_m3"

    # ── Ollama ───────────────────────────────────────────────
    LLM_PROVIDER: str = "ollama"

    OLLAMA_BASE_URL: str = "http://ollama:11434"

    # LLM used for answer generation
    LLM_MODEL: str = "mistral:latest"

    # Embedding model used for query embedding
    EMBEDDING_MODEL: str = "bge-m3"

    # ── RAG ──────────────────────────────────────────────────
    TOP_K_RESULTS: int = 5

    # Minimum Qdrant cosine similarity.
    # Start with None/0.0 if you are not yet calibrated.
    SIMILARITY_THRESHOLD: float = 0.0

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()