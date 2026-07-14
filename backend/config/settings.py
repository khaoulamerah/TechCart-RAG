"""
backend/config/settings.py

Configuration centralisée via variables d'environnement.
Pydantic Settings lit automatiquement le fichier .env
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    """
    Toute la configuration de l'application en un seul endroit.
    
    Pydantic Settings :
    1. Lit les variables depuis .env
    2. Les valide automatiquement
    3. Les type-check
    
    Si une variable obligatoire manque → erreur claire au démarrage.
    """
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    
    # ── Project ───────────────────────────────────────────────
    project_name: str = "TechCart"
    environment: str  = "development"
    debug: bool       = False
    log_level: str    = "INFO"
    
    # ── API ───────────────────────────────────────────────────
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    # ── PostgreSQL ────────────────────────────────────────────
    database_url: str = Field(
        default="postgresql+asyncpg://techcart_user:techcart_secret_2024@localhost:5432/techcart",
        description="Full async database URL"
    )
    
    # ── ChromaDB ──────────────────────────────────────────────
    chroma_host: str         = "localhost"
    chroma_port: int         = 8001
    chroma_persist_dir: str  = "./data/vector_db"
    
    # ── Ollama ────────────────────────────────────────────────
    ollama_base_url: str = "http://localhost:11434"
    llm_model: str       = "mistral:7b-instruct"
    embedding_model: str = "BAAI/bge-m3"
    
    # ── RAG ───────────────────────────────────────────────────
    chunk_size: int              = 512
    chunk_overlap: int           = 100
    top_k_results: int           = 5
    similarity_threshold: float  = 0.7


# Instance globale — importée partout dans l'app
settings = Settings()