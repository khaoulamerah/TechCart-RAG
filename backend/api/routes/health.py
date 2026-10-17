import logging

import httpx
from fastapi import APIRouter

from backend.config.settings import settings
from backend.database.mongodb import mongodb

logger = logging.getLogger("techcart.health")
router = APIRouter(tags=["health"])


async def _check_url(url: str) -> str:
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            response = await client.get(url)
            response.raise_for_status()
        return "ok"
    except Exception:
        return "unavailable"


async def check_ollama() -> str:
    return await _check_url(f"{settings.OLLAMA_BASE_URL}/api/tags")


async def check_qdrant() -> str:
    return await _check_url(
        f"http://{settings.QDRANT_HOST}:{settings.QDRANT_PORT}/collections"
    )


async def check_reranker() -> str:
    if not settings.RERANKER_ENABLED:
        return "disabled"
    return await _check_url(f"{settings.RERANKER_BASE_URL}/health/ready")


@router.get("/health")
async def health() -> dict:
    services = {
        "backend": "ok",
        "mongodb": "ok" if mongodb.db is not None else "unavailable",
        "qdrant": await check_qdrant(),
        "ollama": await check_ollama(),
        "reranker": await check_reranker(),
    }
    required_statuses = {"ok", "disabled"}
    overall_status = (
        "ok"
        if all(value in required_statuses for value in services.values())
        else "degraded"
    )
    return {"status": overall_status, "services": services}
