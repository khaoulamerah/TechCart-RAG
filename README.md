# TechCart — E-commerce RAG Chatbot

TechCart is an e-commerce question-answering chatbot built with **Retrieval-Augmented Generation (RAG)**. It retrieves relevant information from the project's indexed store documentation, policies, FAQs, and guides, then uses a language model to generate a context-aware response.

The application includes a web chat interface, conversation persistence, a developer interface for inspecting conversations and RAG traces, and a separately hosted reranking API.

> **Project status:** This README documents the standard Docker Compose setup in `docker-compose.yml`. The alternative `docker-compose.gpu.yml` is present in the repository, but the standard documented setup is the recommended starting point.

## Table of contents

- [Features](#features)
- [Architecture](#architecture)
- [Technology stack](#technology-stack)
- [Repository structure](#repository-structure)
- [Prerequisites](#prerequisites)
- [Configuration](#configuration)
- [Run with Docker Compose](#run-with-docker-compose)
- [Index the knowledge base](#index-the-knowledge-base)
- [Access the application](#access-the-application)
- [API overview](#api-overview)
- [Tests](#tests)
- [Useful Docker commands](#useful-docker-commands)
- [Troubleshooting](#troubleshooting)
- [Security and data persistence](#security-and-data-persistence)

## Features

- **RAG-based answers:** retrieves relevant text chunks from a Qdrant vector collection before generating an answer.
- **Streaming chat:** the chat API streams response events using Server-Sent Events (SSE).
- **Conversation persistence:** MongoDB stores conversations and messages.
- **Vector search:** Qdrant stores the embedded knowledge-base chunks.
- **LLM and embeddings through Ollama:** the default configuration uses `mistral:latest` for generation and `bge-m3` for embeddings.
- **Dedicated reranker service:** `Qwen/Qwen3-Reranker-0.6B` runs in a separate FastAPI container using Transformers. The backend calls it over the internal Docker network.
- **Document preparation:** a pipeline supports loading, cleaning, validating, deriving, and saving Markdown/CSV data, followed by chunking and indexing steps.
- **Developer interface and traces:** inspect stored conversations and RAG traces to help debug retrieval and response generation.
- **Evaluation utilities:** scripts under `tests/evaluation/` support embedding and retrieval experiments.

## Architecture

```text
User
  |
  v
Web browser
  |
  v
Frontend: HTML / CSS / JavaScript
served by Nginx on port 3000
  |
  | /api/* requests are proxied to FastAPI
  v
Backend: FastAPI on port 8000
  |
  +---- MongoDB ---------------- conversations, messages, RAG traces
  |
  +---- Ollama ----------------- LLM generation + query/document embeddings
  |       `-- mistral:latest
  |       `-- bge-m3
  |
  +---- Qdrant ----------------- vector retrieval
  |
  `---- Reranker HTTP service -- Qwen3-Reranker-0.6B, Transformers, port 8001
```

### Request flow

1. The user submits a question through the web interface.
2. The backend embeds the query using the configured embedding model.
3. The retriever searches the configured Qdrant collection for candidate chunks.
4. When enabled, the backend sends those candidates to the separate reranker service, which scores them for relevance and returns the highest-ranked results.
5. The backend builds the prompt with the retrieved context and asks Ollama to generate the response.
6. The response is streamed to the frontend. Conversation data and RAG traces are stored in MongoDB where applicable.

The reranker is **not an Ollama model** in the standard configuration. It is loaded by Transformers in the `reranker` service and accessed by the backend at `http://reranker:8001` through Docker's internal network.

## Technology stack

| Component | Role |
|---|---|
| Python 3.11 | Backend and reranker runtime |
| FastAPI + Uvicorn | Backend REST/SSE API and reranker API |
| HTML, CSS, JavaScript | Frontend interface |
| Nginx | Frontend web server and `/api/` reverse proxy |
| MongoDB | Conversations, messages, and RAG trace persistence |
| Qdrant | Vector database and semantic retrieval |
| Ollama | LLM inference and embedding model serving |
| Transformers + PyTorch CPU | Dedicated Qwen3 reranking service |
| Docker Compose | Local multi-container environment |
| pytest | Automated tests |

## Repository structure

```text
.
├── backend/
│   ├── api/                  # FastAPI app, routes, and request/response schemas
│   ├── config/               # Environment-based application settings
│   ├── database/             # MongoDB connection lifecycle
│   ├── models/               # Domain/data models
│   ├── repositories/         # Conversation and RAG-trace persistence
│   ├── services/             # Chat, conversation, and developer services
│   └── rag/
│       ├── data_pipelines/   # Load, clean, validate, derive, and save stages
│       ├── embeddings/       # Embedding interfaces and Ollama adapter
│       ├── generator/        # LLM provider and response generation
│       ├── ingestion/        # Documents, chunking, and indexing
│       ├── reranker/         # Reranker interface and HTTP client
│       ├── retriever/        # Retrieval workflow and factory
│       └── vector_store/     # Qdrant adapter
├── data/
│   ├── raw/                  # Raw source datasets
│   ├── semi_structured/      # Markdown source documents for ingestion
│   └── processed/            # Processed documents, chunks, embeddings, evaluation data
├── docker/
│   ├── Dockerfile.backend
│   ├── Dockerfile.frontend
│   └── nginx.conf
├── frontend/
│   ├── assets/css/            # Main, chat, developer, and responsive styles
│   ├── assets/js/             # Chat, API, UI, and developer-interface scripts
│   └── index.html
├── services/
│   └── reranker/              # Standalone Qwen3 reranker API and dependencies
├── scripts/                   # Model initialization, indexing, and maintenance scripts
├── tests/                     # Unit/integration tests and evaluation tools
├── docker-compose.yml         # Standard multi-container configuration
├── docker-compose.gpu.yml     # Alternative GPU-oriented configuration
├── requirements.txt           # Backend Python dependencies
├── .env.example               # Environment-variable template
└── README.md
```

## Prerequisites

Install the following on the host machine:

- Docker Engine
- Docker Compose v2 (`docker compose` command)
- Internet access for the first image builds and model downloads
- Enough available disk space and RAM for the Docker images, the language model, the embedding model, and the reranker

The standard Compose configuration runs the reranker on **CPU by default**. First startup can take several minutes while Docker images and model files are downloaded and the models are initialized.

## Configuration

### 1. Create the local environment file

From the project root:

```bash
cp .env.example .env
```

Edit `.env` and review at least these settings:
The credentials in `.env.example` are **development examples, not production secrets**. Use private credentials for your local `.env`, and do not commit `.env` to version control.

## Run with Docker Compose

Run all commands from the repository root.

### 1. Validate the Compose configuration

```bash
docker compose config --quiet
```

If this command reports missing variables, confirm that you created `.env` and that required values are set.

### 2. Build and start the services

```bash
docker compose up -d --build
```

This starts the following services:

- `mongodb` — persistent conversation and trace data
- `qdrant` — vector search database
- `ollama` — pulls/serves the configured LLM and embedding models
- `reranker` — downloads and loads the configured Hugging Face reranker
- `backend` — FastAPI application
- `frontend` — Nginx and the browser interface

### 3. Watch initialization logs

```bash
docker compose ps
docker compose logs -f ollama
docker compose logs -f reranker
```

Ollama and the reranker may need extra time on the first run. Wait for their health checks to pass before testing RAG requests. Press `Ctrl+C` to stop following logs; it does not stop the containers.

### 4. Check application health

```bash
curl http://localhost:8000/health
```

The health endpoint reports the status of the backend and its dependencies. A `degraded` status usually means that at least one dependency is not available or has not finished initializing.

You can also verify the reranker from inside its container:

```bash
docker compose exec reranker python -c \
"import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:8001/health/ready', timeout=5).read().decode())"
```

Expected response once its model is loaded:

```json
{"status":"ready"}
```

### 5. Open the interface

Open [http://localhost:3000](http://localhost:3000) in a browser. The frontend's `/api/` routes are proxied to the backend by Nginx.

## Index the knowledge base

The repository contains Markdown source documents under `data/semi_structured/`, including store information, FAQs, buying guides, and policies. The script `scripts/reindex_markdown.py` runs the data-preparation pipeline, chunks the processed Markdown, generates embeddings with Ollama, and writes vectors to the configured Qdrant collection.

After the services and configured Ollama models are ready, run:

```bash
docker compose exec backend python scripts/reindex_markdown.py
```

**Important:** this script recreates the configured Qdrant collection before indexing. Run it only when you intend to replace the contents of that collection. If the collection already contains data you need to preserve, back it up or use an appropriate non-destructive indexing workflow instead.

The embedding model used for indexing must match the model and vector configuration expected by the selected collection. With the example configuration, that is `bge-m3` and `techcart_bge_m3`.

## Access the application

| Resource | URL | Description |
|---|---|---|
| Frontend | [http://localhost:3000](http://localhost:3000) | Chat and developer interface |
| Backend API docs | [http://localhost:8000/docs](http://localhost:8000/docs) | Interactive Swagger documentation |
| Backend health | [http://localhost:8000/health](http://localhost:8000/health) | Backend/dependency health summary |
| Frontend-proxied health | [http://localhost:3000/api/health](http://localhost:3000/api/health) | Same health endpoint through Nginx |
| Qdrant dashboard/API | [http://localhost:6333](http://localhost:6333) | Qdrant HTTP API |
| Ollama API | [http://localhost:11434](http://localhost:11434) | Ollama HTTP API |

The reranker listens on port `8001` inside the Docker network. It is not published to the host by the standard Compose file; the backend accesses it using `http://reranker:8001`.

## API overview

The primary backend API is implemented in `backend/api/routes/`.

| Endpoint | Method | Purpose |
|---|---|---|
| `/` | `GET` | Backend welcome/status response |
| `/health` | `GET` | Dependency health report |
| `/chat` | `POST` | Send a chat message; response is streamed as SSE events |
| `/chat/conversations` | `GET` | List chat conversations |
| `/chat/conversations/{conversation_id}` | `GET` / `DELETE` | Retrieve or delete a chat conversation |
| `/conversations` | `GET` / `POST` | List or create conversations |
| `/conversations/{conversation_id}` | `GET` / `PUT` / `DELETE` | Retrieve, update, or delete a conversation |
| `/developer/conversations` | `GET` | List conversations for the developer interface |
| `/developer/conversations/{conversation_id}/traces` | `GET` | Retrieve RAG traces for a conversation |
| `/developer/traces` | `GET` | List recent RAG traces |

The standalone reranker service provides:

| Endpoint | Method | Purpose |
|---|---|---|
| `/health/live` | `GET` | Confirms that the reranker HTTP process is alive |
| `/health/ready` | `GET` | Returns ready only after the model has loaded and warmed up |
| `/rerank` | `POST` | Scores candidate documents and returns them in descending relevance order |

## Tests

The project includes unit and integration-oriented tests under `tests/`, including tests for chunking, the data pipeline, retrieval components, and the HTTP reranker contract.

With a Python environment that has the dependencies in `requirements.txt` installed, run tests from the project root:

```bash
python -m pytest -q tests/
```

Some tests may require reachable services or preconfigured test data. For a focused check of the HTTP reranker client and contract, use:

```bash
PYTHONPATH=. python -m pytest -q \
  tests/test_http_reranker.py \
  tests/test_reranker_contract.py \
  tests/test_reranker_model_format.py
```

For API exploration, use the Swagger UI at `http://localhost:8000/docs` after the backend starts.

## Useful Docker commands

```bash
# Show container status
docker compose ps

# Follow backend logs
docker compose logs -f backend

# Follow reranker logs
docker compose logs -f reranker

# Show the last 100 backend log lines
docker compose logs --tail=100 backend

# Restart one service
docker compose restart backend

# Stop containers but preserve named volumes
docker compose down

# Start again
docker compose up -d
```

Avoid `docker compose down -v` unless you intentionally want to delete named volumes. Those volumes hold MongoDB data, Qdrant storage, downloaded Ollama models, and the reranker Hugging Face cache.

## Troubleshooting

### The frontend does not load

```bash
docker compose ps
docker compose logs --tail=100 frontend
```

Confirm that `http://localhost:3000` is available and that the `frontend` service mounts `./frontend` at `/usr/share/nginx/html` as defined in `docker-compose.yml`.

### Backend health is `degraded`

```bash
docker compose ps
docker compose logs --tail=100 backend
docker compose logs --tail=100 mongodb qdrant ollama reranker
```

Wait for `ollama` and `reranker` to finish loading, then check `/health` again. Verify that `.env` has the expected model and collection names.

### The reranker is not ready

```bash
docker compose logs --tail=150 reranker
docker compose exec reranker python -c \
"import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:8001/health/ready', timeout=5).read().decode())"
```

The first startup downloads model files from Hugging Face and therefore needs working network/DNS. Check available RAM and disk space if the container repeatedly restarts. The `reranker_cache` volume allows downloaded model files to be reused on later starts.

### Ollama model downloads are taking a long time

```bash
docker compose logs -f ollama
docker compose exec ollama ollama list
```

The initialization script pulls the configured `LLM_MODEL` and `EMBEDDING_MODEL` if they are not already available in the persistent Ollama volume.

### The chatbot responds without useful document context

Check that the selected Qdrant collection exists and contains vectors. If it is empty, follow [Index the knowledge base](#index-the-knowledge-base). Also verify that the `EMBEDDING_MODEL` matches the vector collection's embedding configuration.

## Security and data persistence

- Keep `.env` private and never commit production credentials.
- The published ports in the default Compose configuration are intended for local development. Review port exposure, authentication, TLS, CORS, and secret management before deploying publicly.
- Named Docker volumes persist data across container restarts and ordinary `docker compose down` operations.
- `docker compose down -v` deletes named volumes and may permanently remove local conversation data, vector data, and cached model files.
- Treat retrieved documents and model responses as application data that should be validated and monitored; RAG does not guarantee that every answer is correct.

---

## Development notes

- Backend application entry point: `backend/api/main.py`
- Backend configuration: `.env` and `backend/config/settings.py`
- Main Compose configuration: `docker-compose.yml`
- Nginx routing configuration: `docker/nginx.conf`
- Reranker API: `services/reranker/app.py`
- Reranker dependencies: `services/reranker/requirements.txt`
- Markdown reindex script: `scripts/reindex_markdown.py`
- Evaluation utilities: `tests/evaluation/`
