# Apply the TechCart Ollama reranker patch

1. Back up your project.
2. Extract this ZIP over the existing `ecommerce-rag-chatbot` project root so the included paths overwrite their existing counterparts.
3. Delete `backend/rag/reranker/bge.py` as listed in `DELETE_FILES.txt`.
4. Edit your existing `.env` file manually. Do not replace it with `.env.example`; keep your credentials and update the reranker values as shown in `OLLAMA_RERANKER_MIGRATION.md`.
5. From the project root, run `docker compose config --quiet`, then `docker compose up -d --build`.
6. Follow the smoke-test commands in `OLLAMA_RERANKER_MIGRATION.md`.

This patch intentionally does not contain `.env` or `.git`.
