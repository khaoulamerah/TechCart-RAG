import logging

import httpx
from fastapi import APIRouter

from backend.config.settings import settings
from backend.database.mongodb import mongodb

logger = logging.getLogger("techcart.health")

router = APIRouter(tags=["health"])


async def check_ollama() -> str:
    try:
        async with httpx.AsyncClient(
            timeout=3.0
        ) as client:

            response = await client.get(
                f"{settings.OLLAMA_BASE_URL}/api/tags"
            )

            response.raise_for_status()

        return "ok"

    except Exception:
        return "unavailable"


async def check_qdrant() -> str:
    try:
        async with httpx.AsyncClient(
            timeout=3.0
        ) as client:

            response = await client.get(
                f"http://{settings.QDRANT_HOST}:{settings.QDRANT_PORT}/collections"
            )

            response.raise_for_status()

        return "ok"

    except Exception:
        return "unavailable"


@router.get("/health")
async def health() -> dict:
    mongo_status = (
        "ok"
        if mongodb.db is not None
        else "unavailable"
    )

    qdrant_status = await check_qdrant()
    ollama_status = await check_ollama()

    return {
        "status": "ok",
        "services": {
            "backend": "ok",
            "mongodb": mongo_status,
            "qdrant": qdrant_status,
            "ollama": ollama_status,
        },
    }