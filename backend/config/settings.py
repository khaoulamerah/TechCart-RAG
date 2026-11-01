from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "TechCart"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000

    # MongoDB
    MONGODB_URL: str
    MONGODB_DB: str = "techcart"

    # Qdrant
    QDRANT_HOST: str = "qdrant"
    QDRANT_PORT: int = 6333
    QDRANT_GRPC_PORT: int = 6334
    QDRANT_COLLECTION: str = "techcart_bge_m3"

    # Ollama
    LLM_PROVIDER: str = "ollama"
    OLLAMA_BASE_URL: str = "http://ollama:11434"
    LLM_MODEL: str = "mistral:latest"
    EMBEDDING_MODEL: str = "bge-m3"

    RERANKER_ENABLED: bool = True
    RERANKER_PROVIDER: str = "http"
    RERANKER_BASE_URL: str = "http://reranker:8001"
    RERANKER_MODEL: str = "Qwen/Qwen3-Reranker-0.6B"
    RERANKER_TIMEOUT_SECONDS: float = 60.0

    # Retrieval
    RETRIEVAL_K: int = 10
    TOP_K_RESULTS: int = 5
    RETRIEVAL_TIMEOUT_SECONDS: int = 180

    SIMILARITY_THRESHOLD: float = 0.0

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
