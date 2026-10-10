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
