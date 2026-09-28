from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    PROJECT_NAME: str = "TechCart"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000

    # ─────────────────────────────────────────────
    # MONGODB
    # ─────────────────────────────────────────────
    MONGODB_URL: str
    MONGODB_DB: str = "techcart"

    # ─────────────────────────────────────────────
    # QDRANT
    # ─────────────────────────────────────────────
    QDRANT_HOST: str = "qdrant"
    QDRANT_PORT: int = 6333
    QDRANT_GRPC_PORT: int = 6334
    QDRANT_COLLECTION: str = "techcart_bge_m3"

    # ─────────────────────────────────────────────
    # OLLAMA
    # ─────────────────────────────────────────────
    LLM_PROVIDER: str = "ollama"
    OLLAMA_BASE_URL: str = "http://ollama:11434"
    LLM_MODEL: str = "mistral:latest"
    EMBEDDING_MODEL: str = "bge-m3"

    # ─────────────────────────────────────────────
    # RERANKER
    # ─────────────────────────────────────────────
    RERANKER_MODEL: str = (
        "BAAI/bge-reranker-v2-m3"
    )

    RERANKER_USE_FP16: bool = False

    # ─────────────────────────────────────────────
    # RETRIEVAL
    # ─────────────────────────────────────────────
    # Number of candidates retrieved from Qdrant
    # before reranking.
    RETRIEVAL_K: int = 20

    # Final number of chunks sent to the RAG prompt.
    TOP_K_RESULTS: int = 5

    # Currently not used as a hard filter.
    # Keep at 0 until properly calibrated.
    SIMILARITY_THRESHOLD: float = 0.0

    # ─────────────────────────────────────────────
    # PYDANTIC SETTINGS
    # ─────────────────────────────────────────────
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()