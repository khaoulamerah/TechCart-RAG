from __future__ import annotations

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, HTTPException, status

from model import Qwen3RerankerModel
from schemas import RerankRequest, RerankResponse

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger("techcart.reranker.api")

RERANKER_ENABLED = os.getenv("RERANKER_ENABLED", "true").strip().lower() in {
    "1", "true", "yes", "on"
}
MODEL_NAME = os.getenv("RERANKER_MODEL", "Qwen/Qwen3-Reranker-0.6B")
MODEL_DEVICE = os.getenv("RERANKER_DEVICE", "cpu")
MODEL_MAX_LENGTH = int(os.getenv("RERANKER_MAX_LENGTH", "2048"))
MODEL_INSTRUCTION = os.getenv(
    "RERANKER_INSTRUCTION",
    "Given a web search query, retrieve relevant passages that answer the query",
)
MODEL_MAX_DOCUMENT_CHARS = int(os.getenv("RERANKER_MAX_DOCUMENT_CHARS", "12000"))
WARMUP_RETRY_SECONDS = int(os.getenv("RERANKER_WARMUP_RETRY_SECONDS", "60"))

reranker = Qwen3RerankerModel(
    model_name=MODEL_NAME,
    device=MODEL_DEVICE,
    max_length=MODEL_MAX_LENGTH,
    instruction=MODEL_INSTRUCTION,
    max_document_chars=MODEL_MAX_DOCUMENT_CHARS,
)


async def warmup_until_ready() -> None:
    """Load model in the background; keep the API alive if HF is unavailable."""
    if not RERANKER_ENABLED:
        logger.info("Reranker is disabled by RERANKER_ENABLED=false; skipping model download.")
        return

    while not reranker.is_ready:
        try:
            logger.info("Starting Qwen3 reranker warm-up for model %s", MODEL_NAME)
            await asyncio.to_thread(reranker.warm_up)
            logger.info("Qwen3 reranker is ready.")
            return
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception(
                "Reranker model could not be loaded. Chat will fall back to vector ranking; "
                "retrying in %s seconds.",
                WARMUP_RETRY_SECONDS,
            )
            await asyncio.sleep(max(10, WARMUP_RETRY_SECONDS))


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    warmup_task = asyncio.create_task(warmup_until_ready())
    try:
        yield
    finally:
        warmup_task.cancel()
        await asyncio.gather(warmup_task, return_exceptions=True)


app = FastAPI(
    title="TechCart Reranker Service",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health/live")
def health_live() -> dict[str, str]:
    return {"status": "live"}


@app.get("/health/ready")
def health_ready() -> dict[str, str]:
    if not RERANKER_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Reranker is disabled by configuration.",
        )
    if not reranker.is_ready:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Reranker model is not ready yet.",
        )
    return {"status": "ready", "model": MODEL_NAME}


@app.post("/rerank", response_model=RerankResponse)
async def rerank(request: RerankRequest) -> RerankResponse:
    if not RERANKER_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Reranker is disabled by configuration.",
        )
    if not reranker.is_ready:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Reranker model is not ready yet.",
        )

    try:
        documents = await asyncio.to_thread(
            reranker.rerank,
            request.query,
            request.documents,
            request.top_k,
        )
    except Exception as exc:
        logger.exception("Reranking request failed.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Reranking failed.",
        ) from exc

    return RerankResponse(documents=documents, model=MODEL_NAME)
