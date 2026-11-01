# TechCart RAG Chatbot: Project Guide

A step-by-step explanation of the project: architecture, request flow, endpoints, functions, data and how to run it. Written from the project archive `ecommerce-rag-chatbot` (state of November 2026).

## 1. What the project is

TechCart is a chatbot for a fictional computer-hardware store. A visitor types a question in the browser. The backend searches the store’s knowledge base (policies, FAQ, buying guide), picks the most relevant passages, and asks a local language model to write an answer **using only those passages**. This technique is called **RAG** (Retrieval-Augmented Generation).

Everything runs locally in Docker, with no external AI API. There are two interfaces:

- **Chat UI** at `/`: the customer-facing chat with streamed answers and a conversation history sidebar.
- **Developer UI** at `/developer`: an observability page that shows, for every answer, the retrieved chunks, the rerank scores, the final prompt, the LLM response and timings.

## 2. Architecture at a glance

| Service | Technology | Port | Role |
| --- | --- | --- | --- |
| frontend | Nginx + vanilla JavaScript | 3000 (container 80) | Serves the UI and proxies `/api/*` to the backend |
| backend | FastAPI (Python 3.11) | 8000 | REST + SSE API, orchestrates the RAG pipeline |
| mongodb | MongoDB | 27017 | Stores conversations and RAG traces |
| qdrant | Qdrant vector database | 6333 (HTTP), 6334 (gRPC) | Similarity search over chunk embeddings |
| ollama | Ollama | 11434 | Runs the chat LLM (`mistral:latest`) and the embedding model (`bge-m3`) |
| reranker | FastAPI + Transformers | 8001 (127.0.0.1 only) | Re-scores candidates with `Qwen/Qwen3-Reranker-0.6B` |

```
Browser ──► Nginx :3000 ──/api/──► FastAPI backend :8000
                                      ├─► MongoDB   (history, traces)
                                      ├─► Ollama    (embed the question, generate the answer)
                                      ├─► Qdrant    (vector search)
                                      └─► Reranker  (re-order the candidates)
```

## 3. Life of one chat request

1. The browser sends `POST /api/chat` with `{message, session_id, conversation_id}`. Nginx strips `/api` and forwards it to the backend.
2. The route `send_chat_message` opens a streaming response (Server-Sent Events) and calls `ChatService.stream_message`.
3. `prepare_conversation` validates the message, then finds the conversation by `conversation_id`, or finds or creates one by `session_id`.
4. The user message is saved in MongoDB and a `metadata` event is sent right away so the UI can show the request as accepted.
5. **Retrieval** runs in a worker thread (`Retriever.retrieve_with_trace`): the question is embedded by Ollama (`bge-m3`), then Qdrant returns the `RETRIEVAL_K` (10) nearest chunks.
6. **Reranking**: the candidates are sent to the reranker service, which scores each (question, chunk) pair and keeps the best `TOP_K_RESULTS` (5). If the reranker is unreachable, the backend falls back to the vector-search order.
7. While this runs, the backend emits `status` events every \~2 seconds (“Recherche des documents pertinents…”, etc.).
8. `build_rag_prompt` assembles the system instruction, the retrieved chunks and the question into one prompt.
9. **Generation**: the prompt is streamed to Ollama through `ChatOllama.astream`. Every piece of text is forwarded to the browser as a `token` event.
10. The full answer is saved as an assistant message, a **trace** document (timings, chunks, scores, prompt, response) is saved in `rag_traces`, and a final `done` event closes the stream.
11. On any failure an `error` event is emitted instead, and the trace is saved with `status: "error"`.

## 4. Repository map

```
ecommerce-rag-chatbot/
├── backend/
│   ├── api/            main.py (app + lifespan), routes/, schemas/
│   ├── config/         settings.py (environment variables)
│   ├── database/       mongodb.py (connection + indexes)
│   ├── models/         conversation.py (Pydantic models)
│   ├── repositories/   conversation.py, rag_trace.py (MongoDB access)
│   ├── services/       chat.py, conversation.py, developer.py (business logic)
│   └── rag/
│       ├── data_pipelines/  Load → Clean → Validate → Derive → Save
│       ├── ingestion/       document.py, chunker.py, chunking/, indexer.py
│       ├── embeddings/      embedder.py (Ollama), models.py
│       ├── vector_store/    qdrant.py
│       ├── retriever/       retriever.py, factory.py
│       ├── reranker/        base.py, http_client.py
│       ├── generator/       ollama_provider.py, factory.py
│       └── prompt.py
├── services/reranker/   standalone reranker microservice (app.py, model.py, schemas.py)
├── frontend/            index.html + assets/js + assets/css
├── scripts/             reindex_markdown.py, index_qdrant.py, ollama.sh
├── data/                raw/, semi_structured/ (source .md), processed/, vector_db/
├── tests/               unit tests + evaluation/ (embedding benchmark)
├── docker/              Dockerfile.backend, Dockerfile.frontend, nginx.conf
└── docker-compose.yml   (and docker-compose.gpu.yml for NVIDIA GPUs)
```

The backend follows a layered design: **route → service → repository**. Routes only handle HTTP, services hold the logic, repositories talk to MongoDB.

## 5. Configuration (`.env`)

Settings are read by `backend/config/settings.py` (pydantic-settings).

| Variable | Example | Meaning |
| --- | --- | --- |
| `MONGODB_URL`, `MONGODB_DB` | `mongodb://…@mongodb:27017/techcart` | MongoDB connection |
| `QDRANT_HOST`, `QDRANT_PORT`, `QDRANT_COLLECTION` | `qdrant`, `6333`, `techcart_bge_m3` | Vector database and collection name |
| `LLM_PROVIDER`, `LLM_MODEL`, `OLLAMA_BASE_URL` | `ollama`, `mistral:latest` | Chat model |
| `EMBEDDING_MODEL` | `bge-m3` | Must match the model used at indexing time |
| `RERANKER_ENABLED`, `RERANKER_BASE_URL`, `RERANKER_MODEL`, `RERANKER_TIMEOUT_SECONDS` | `true`, `http://reranker:8001` | Reranker client settings |
| `RETRIEVAL_K` / `TOP_K_RESULTS` | `10` / `5` | Candidates fetched / chunks kept for the prompt |
| `RETRIEVAL_TIMEOUT_SECONDS` | `180` | Max time for retrieval + reranking |
| `SIMILARITY_THRESHOLD` | `0.0` | Declared but not used yet |
| `RERANKER_DEVICE`, `RERANKER_MAX_LENGTH`, … | `cpu`, `2048` | Read by the reranker container only |

## 6. Backend, module by module

### 6.1 `api/main.py`

| Function | Purpose |
| --- | --- |
| `lifespan(app)` | On startup: connects to MongoDB, then launches a background task that warms up the LLM and then the reranker. On shutdown: cancels the task and closes MongoDB. |
| `warmup_llm()` | Sends a one-token request so Ollama loads the model into memory before the first user. |
| `warmup_reranker()` | Calls the reranker’s warm-up in a thread. |
| `root()` | `GET /` health-style message. |

CORS allows `localhost:3000` and `localhost:8000`.

### 6.2 Services

**`ChatService`** (`services/chat.py`) is the heart of the application.

| Method | Purpose |
| --- | --- |
| `prepare_conversation` | Validates the message and resolves or creates the conversation and session. |
| `stream_message` | The full RAG flow described in section 3. An async generator that yields event dictionaries. |
| `_stream_llm_with_progress` | Wraps the LLM stream and yields a keep-alive `status` event if no token arrives for 5 seconds. |
| `_context_from_results` | Formats retrieved chunks as text for the trace. |
| `_save_trace` | Saves the trace; never allowed to break the chat. |

**`ConversationService`** (`services/conversation.py`): `create_conversation`, `get_conversation`, `get_conversation_by_session`, `get_or_create_by_session`, `list_conversations`, `update_conversation`, `delete_conversation`, `add_message`, `get_messages`, `update_message`, `delete_message`, plus `serialize_conversation` (Mongo document to JSON-friendly dict).

**`DeveloperService`** (`services/developer.py`): `list_conversations`, `get_conversation`, `get_trace`, `get_conversation_traces`, `get_recent_traces`.

### 6.3 Repositories

- `ConversationRepository`: `create`, `get_by_id`, `get_by_session_id`, `get_by_user_id`, `list_conversations`, `update`, `delete`, `add_message` (`$push`), `get_messages`, `update_message`, `delete_message` (`$pull`).
- `RAGTraceRepository`: `create`, `get_by_id`, `get_by_conversation`, `get_recent`.
- `database/mongodb.py`: `connect_to_mongo`, `close_mongo_connection`, `create_indexes`, `get_database`.

### 6.4 RAG components

| Component | Key functions | Notes |
| --- | --- | --- |
| `Retriever` | `retrieve_with_trace(query)`, `retrieve(query)` | Embeds the query, searches Qdrant, optionally reranks, and returns documents plus a timing/score trace. |
| `get_retriever()` | cached factory | Builds embedder, vector store and reranker from settings. |
| `OllamaEmbeddingStrategy` | `embed(texts)` | Calls Ollama’s embed API; checks the count of returned vectors. |
| `QdrantVectorStore` | `collection_exists`, `create_collection`, `delete_collection`, `recreate_collection`, `upsert`, `search` | Cosine distance. |
| `HttpReranker` | `rerank(query, documents, top_k)` | POSTs to the reranker service; falls back to vector scores on any error. |
| `OllamaLLMProvider` | `warm_up()`, `generate_stream(prompt)` | Streams tokens via LangChain `ChatOllama`. |
| `get_llm_provider()` | cached factory | Only `ollama` is supported today. |
| `build_rag_prompt(question, results)` |  | System rules + numbered context blocks + question. |

The prompt tells the model to answer only from the context, never invent products, prices or policies, say so when the information is missing, and reply in the user’s language.

## 7. API reference

Interactive docs are available at `http://localhost:8000/docs` (Swagger).

### 7.1 Chat (streaming)

`POST /chat`, body:

```json
{ "message": "What is the return policy?", "session_id": null, "conversation_id": null }
```

`message` is required (1 to 4000 characters). The response is `text/event-stream`. Each event looks like `event: <type>` followed by `data: {json}`.

| Event | Payload | Meaning |
| --- | --- | --- |
| `metadata` | `conversation_id`, `session_id` | Request accepted; IDs to reuse in the next call |
| `status` | `message` | Progress text for the “thinking” indicator |
| `token` | `content` | A piece of the answer |
| `done` | `conversation_id`, `session_id`, `created_at` | Answer finished and saved |
| `error` | `message`, `detail` | Something failed |

### 7.2 Conversations

| Method and path | Purpose | Success |
| --- | --- | --- |
| `POST /conversations` | Create (`session_id` required; optional `title`, `user_id`, `is_guest`, `metadata`) | 201 |
| `GET /conversations?skip=0&limit=20` | Paginated list (`limit` 1 to 100) | 200 |
| `GET /conversations/{id}` | One conversation with its messages | 200 |
| `PUT /conversations/{id}` | Update `title`, `user_id`, `is_guest`, `metadata` | 200 |
| `DELETE /conversations/{id}` | Delete | 204 |
| `POST /conversations/{id}/messages` | Add a message (`role` is `user` or `assistant`, `content`) | 201 |
| `GET /conversations/{id}/messages` | List messages | 200 |
| `PUT /conversations/{id}/messages/{message_id}` | Edit `content` or `metadata` | 200 |
| `DELETE /conversations/{id}/messages/{message_id}` | Remove a message | 200 |
| `GET /chat/conversations`, `GET` and `DELETE /chat/conversations/{id}` | Aliases used by the chat UI | 200 / 204 |

Errors: 400 (invalid input), 404 (unknown conversation or message).

### 7.3 Developer / observability

| Method and path | Returns |
| --- | --- |
| `GET /developer/conversations?limit=50` | Summaries with `message_count` |
| `GET /developer/conversations/{id}` | Full conversation |
| `GET /developer/conversations/{id}/traces` | All traces of that conversation, oldest first |
| `GET /developer/traces?limit=50` | Most recent traces |
| `GET /developer/traces/{trace_id}` | One trace |

### 7.4 Health

`GET /health` returns `{status, services:{backend, mongodb, qdrant, ollama}}`, where each service is `ok` or `unavailable`.

### 7.5 Reranker service (port 8001)

| Method and path | Purpose |
| --- | --- |
| `GET /health/live` | Process is alive |
| `GET /health/ready` | 200 only once the model is loaded, otherwise 503 |
| `POST /rerank` | Body `{query, documents[], top_k}`; returns `{documents, model}` sorted by `rerank_score` |

## 8. Data model

**MongoDB `conversations`**: `_id`, `session_id` (unique), `user_id`, `title`, `is_guest`, `messages[]`, `created_at`, `updated_at`, `metadata`. Each message holds `message_id`, `role`, `content`, `created_at`, `metadata`.

**MongoDB `rag_traces`**: one document per question with `conversation_id`, `message_id`, `question`, `retrieval` (embedding model, latencies, candidate chunks with scores), `reranking` (model, input and output counts, scores), `llm` (provider, model, time to first token, latency, response), `context`, `prompt`, `total_latency_ms`, `status` and `error`.

**Qdrant point**: id is a deterministic UUID derived from the chunk id; the vector has 1024 dimensions for `bge-m3`; the payload contains `chunk_id`, `document_id`, `text` and `metadata` (`source`, `document_type`, `position`, `chunking_strategy`).

## 9. Building the knowledge base

The command `docker compose exec backend python scripts/reindex_markdown.py` performs five steps. **It deletes and recreates the Qdrant collection.**

1. **Data pipeline** (`data_pipelines/`): for each Markdown file in `data/semi_structured/`, the stages Load, Clean, Validate, Derive and Save run in order. Each stage picks a *strategy* by data type (CSV or Markdown), which is the Strategy pattern. Results land in `data/processed/markdown/`.
2. **Load** the processed files as `Document` objects.
3. **Chunk** with `MarkdownChunkingStrategy` (chunk size 1000 characters): splits at headings, keeps each FAQ question with its answer, and splits oversized sections by paragraph, then sentence, then characters. Output: `data/processed/chunks/markdown_chunks.json` (55 chunks from 7 documents).
4. **Embed** every chunk with `bge-m3` through Ollama and save a JSON backup in `data/processed/embeddings/`.
5. **Index** into Qdrant in batches of 32, then run a verification search.

Other chunkers exist: `CharacterChunkingStrategy` (512 characters, 100 overlap) and `ChonkieSemanticChunkingStrategy` (semantic splitting with the `chonkie` library). `scripts/index_qdrant.py` loads precomputed embeddings from JSON into Qdrant without recomputing them.

The three product CSV files (`All_GPUs.csv`, `Intel_CPUs.csv`, `amd-cpus.csv`) can be cleaned and converted to text by the CSV pipeline, but no script currently indexes them into Qdrant.

## 10. The reranker microservice

A cross-encoder style reranker improves precision over plain vector search. `services/reranker/model.py` (`Qwen3RerankerModel`) loads Qwen3-Reranker-0.6B with Transformers. For each (question, chunk) pair it builds a prompt asking whether the document answers the query, and reads the model’s probability of the answer “yes”. That probability is the `rerank_score`. Documents are scored one by one under a lock to limit memory use on CPU, then sorted and cut to `top_k`.

The model downloads in a background task, so the service starts immediately. `/health/ready` tells when scoring is possible, and the backend simply falls back to vector order until then.

## 11. Frontend

Plain HTML, CSS and JavaScript, no framework. Scripts are loaded in this order:

| File | Responsibility |
| --- | --- |
| `config.js` | `CONFIG`: API base `/api`, timeouts, storage keys, welcome message |
| `api.js` | `TechCartAPI.streamMessage` (reads the SSE stream with `fetch`), `parseSSEEvent`, `deleteConversation`, and the developer API calls |
| `ui.js` | `TechCartUI`: rendering messages, streaming cursor, thinking indicator, history sidebar, toasts, theme. Text is HTML-escaped before a tiny Markdown renderer adds bold and line breaks |
| `chat.js` | `TechCartChat`: send flow (`sendUserMessage`), new, open, rename, pin, share and delete conversations. The history list is kept in the browser’s `localStorage` |
| `app.js` | Wires events and switches between the chat page and the developer page (`/developer`) |
| `developer.js` | `DeveloperApp`: lists conversations and traces and renders retrieval, reranking and LLM panels |

## 12. Evaluation of embedding models

`tests/evaluation/` compares five embedding models on 50 questions, each labelled with its relevant document. Metrics are Recall@1, Recall@5 and MRR@5.

| Model | Recall@1 | Recall@5 | MRR@5 |
| --- | --- | --- | --- |
| **bge-m3** (chosen) | 0.80 | 0.99 | 0.93 |
| qwen3-embedding 0.6b | 0.78 | 0.98 | 0.91 |
| nomic-embed-text-v2-moe | 0.74 | 0.96 | 0.88 |
| snowflake-arctic-embed2 | 0.72 | 0.99 | 0.87 |
| nomic-embed-text | 0.68 | 0.96 | 0.85 |

bge-m3 wins on quality but is slower to embed than the nomic models. The labels point to whole documents, and only the 7 Markdown documents are covered, so this benchmark says nothing yet about product questions.

## 13. Running the project

```bash
cp .env.example .env              # then set your own passwords
docker compose config --quiet     # validate
docker compose up -d --build      # start everything (first run downloads models)
curl http://localhost:8000/health # check dependencies
docker compose exec backend python scripts/reindex_markdown.py   # build the index
```

Then open `http://localhost:3000`. For NVIDIA GPUs use `docker-compose.gpu.yml`. Tests: `python -m pytest -q tests/`.

## 14. Good to know

- Answers depend only on the 7 indexed Markdown documents; product specs from the CSV files are not searchable yet.
- Each question is answered on its own: the chat history is stored but not sent back to the model.
- The API has no authentication, including the developer endpoints.
- A separate document, “Code Review and Fix Guide”, lists the bugs and improvements found in this version.
