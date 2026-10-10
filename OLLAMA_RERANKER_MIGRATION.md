# TechCart: migrate the reranker to local Ollama

This version replaces `FlagEmbedding` / `BAAI/bge-reranker-v2-m3` with the
locally installed model `dengcao/Qwen3-Reranker-0.6B:Q8_0`.

## Configuration

Update the local `.env` (it is intentionally not included in the source ZIP):

```dotenv
RERANKER_ENABLED=true
RERANKER_PROVIDER=ollama
RERANKER_MODEL=dengcao/Qwen3-Reranker-0.6B:Q8_0
RERANKER_TIMEOUT_SECONDS=30
RERANKER_TOP_LOGPROBS=20
RERANKER_INSTRUCTION=Given a web search query, retrieve relevant passages that answer the query
RERANKER_MAX_DOCUMENT_CHARS=12000
RETRIEVAL_TIMEOUT_SECONDS=180
```

Delete the old `RERANKER_USE_FP16` setting. No Hugging Face cache or model
snapshot is needed for the reranker.

After restart, confirm the backend reads the intended model (rather than a
stale value from your existing `.env`):

```bash
docker compose exec backend python -c "from backend.config.settings import settings; print(settings.RERANKER_PROVIDER, settings.RERANKER_MODEL)"
```

Expected model name: `dengcao/Qwen3-Reranker-0.6B:Q8_0`.

## How scoring works

Ollama does not offer a dedicated `/api/rerank` endpoint in the API used by this
project. The adapter submits each query/document pair to Ollama's local
`/api/generate`, using the Qwen3-Reranker prompt format and first-token log
probabilities. It computes the two-class score `P(yes | yes/no)` and sorts the
retrieved Qdrant candidates by that score. If an Ollama response lacks usable
log probabilities, the adapter logs a warning and uses the model's strict
`yes`/`no` output as a binary fallback.

## Apply and restart

From the project root, after replacing the files from this archive:

```bash
docker compose config --quiet
docker compose up -d --build
```

The Ollama entrypoint checks/pulls the LLM, embedding model, and reranker model.
The Ollama healthcheck stays unhealthy until all configured models are ready,
so the backend does not start model warm-up prematurely.

Check startup and model availability:

```bash
docker compose ps
docker compose logs --tail=150 ollama
docker compose logs --tail=150 backend
docker compose exec ollama ollama list
```

Test model scoring without touching Qdrant:

```bash
docker compose exec backend python -c "from backend.config.settings import settings; from backend.rag.reranker.ollama_qwen import OllamaQwenReranker; r = OllamaQwenReranker(model_name=settings.RERANKER_MODEL, base_url=settings.OLLAMA_BASE_URL, timeout_seconds=settings.RERANKER_TIMEOUT_SECONDS, top_logprobs=settings.RERANKER_TOP_LOGPROBS, instruction=settings.RERANKER_INSTRUCTION); r.warm_up(); print('OLLAMA RERANKER OK')"
```

Test the reranker against the Qdrant collection from the backend container:

```bash
docker compose exec backend python tests/test_retriever.py
```

Run the adapter unit tests on your host (activate your project virtual
environment first, if you use one):

```bash
PYTHONPATH=. python -m pytest -q tests/test_ollama_reranker.py
```

The code has a 30-second timeout per Ollama reranker request and a 180-second
overall retrieval timeout. If retrieval exceeds the limit, the stream emits an
error instead of endlessly cycling through progress messages.
