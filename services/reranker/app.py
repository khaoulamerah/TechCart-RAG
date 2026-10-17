"""FastAPI endpoints for the standalone TechCart reranker service."""

from __future__ import annotations

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from math import isfinite
from time import perf_counter
from typing import AsyncIterator

from fastapi import FastAPI, HTTPException, Request

from model import Qwen3Reranker
from schemas import RankedDocument, RerankRequest, RerankResponse

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger("techcart.reranker_service")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Load and warm the model before the service becomes ready."""
    model = Qwen3Reranker(
        model_name=os.getenv("RERANKER_MODEL", "Qwen/Qwen3-Reranker-0.6B"),
        device=os.getenv("RERANKER_DEVICE", "cpu"),
        max_length=int(os.getenv("RERANKER_MAX_LENGTH", "2048")),
        instruction=os.getenv(
            "RERANKER_INSTRUCTION",
            "Given a web search query, retrieve relevant passages that answer the query",
        ),
        max_document_chars=int(os.getenv("RERANKER_MAX_DOCUMENT_CHARS", "12000")),
        batch_size=int(os.getenv("RERANKER_BATCH_SIZE", "2")),
    )

    # Keep model download/load and warm-up off the event loop.
    await asyncio.to_thread(model.warm_up)
    app.state.reranker = model
    logger.info("Reranker service is ready.")
    try:
        yield
    finally:
        app.state.reranker = None
        logger.info("Reranker service is stopping.")


app = FastAPI(
    title="TechCart Reranker API",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health/live")
def health_live() -> dict[str, str]:
    """Liveness check: the HTTP process is serving requests."""
    return {"status": "alive"}


@app.get("/health/ready")
def health_ready(request: Request) -> dict[str, str]:
    """Readiness check: model loading and warm-up have succeeded."""
    if getattr(request.app.state, "reranker", None) is None:
        raise HTTPException(status_code=503, detail="Reranker model is not ready.")
    return {"status": "ready"}


@app.post("/rerank", response_model=RerankResponse)
def rerank(
    payload: RerankRequest,
    request: Request,
) -> RerankResponse:
    """Score and sort document candidates by query relevance."""
    if not payload.query.strip():
        raise HTTPException(status_code=422, detail="Query cannot be blank.")
    if not payload.documents:
        return RerankResponse(results=[])

    indices = [document.index for document in payload.documents]
    if len(indices) != len(set(indices)):
        raise HTTPException(
            status_code=422,
            detail="Document indexes must be unique within a request.",
        )

    reranker: Qwen3Reranker | None = getattr(request.app.state, "reranker", None)
    if reranker is None:
        raise HTTPException(status_code=503, detail="Reranker model is not ready.")

    started = perf_counter()
    try:
        scores = reranker.score_documents(
            payload.query,
            [document.text for document in payload.documents],
        )
        if len(scores) != len(payload.documents):
            raise RuntimeError("Model returned a different number of scores than inputs.")

        results = [
            RankedDocument(index=document.index, score=float(score))
            for document, score in zip(payload.documents, scores, strict=True)
            if isfinite(float(score))
        ]
        if len(results) != len(payload.documents):
            raise RuntimeError("Model returned a non-finite relevance score.")

        results.sort(key=lambda result: result.score, reverse=True)
        selected = results[: min(payload.top_k, len(results))]
        logger.info(
            "Reranked %d documents in %.1f ms; returned %d.",
            len(payload.documents),
            (perf_counter() - started) * 1000,
            len(selected),
        )
        return RerankResponse(results=selected)

    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Reranking request failed.")
        raise HTTPException(status_code=500, detail="Reranking failed.") from exc
