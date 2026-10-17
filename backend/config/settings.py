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

    # Reranker (Qwen3-Reranker served by local Transformers on CPU/GPU)
    RERANKER_ENABLED: bool = False
    RERANKER_PROVIDER: str = "transformers"
    RERANKER_MODEL: str = "Qwen/Qwen3-Reranker-0.6B"
    RERANKER_DEVICE: str = "auto"
    RERANKER_MAX_LENGTH: int = 2048
    RERANKER_INSTRUCTION: str = (
        "Given a web search query, retrieve relevant passages that answer the query"
    )
    RERANKER_MAX_DOCUMENT_CHARS: int = 12000

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
