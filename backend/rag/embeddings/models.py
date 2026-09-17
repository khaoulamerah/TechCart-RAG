EMBEDDING_MODELS: dict[str, str] = {
    "nomic_v1": "nomic-embed-text",
    "bge_m3": "bge-m3",
    "nomic_v2": "nomic-embed-text-v2-moe",
    "qwen3": "qwen3-embedding:0.6b",
    "arctic": "snowflake-arctic-embed2",
}


QDRANT_COLLECTIONS: dict[str, str] = {
    "nomic_v1": "techcart_nomic_v1",
    "bge_m3": "techcart_bge_m3",
    "nomic_v2": "techcart_nomic_v2",
    "qwen3": "techcart_qwen3",
    "arctic": "techcart_arctic",
}