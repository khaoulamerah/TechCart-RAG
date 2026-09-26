import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes import (
    chat,
    conversation,
    health,
)
from backend.database.mongodb import (
    close_mongo_connection,
    connect_to_mongo,
)
from backend.rag.generator.factory import (
    get_llm_provider,
)
from backend.rag.retriever.factory import (
    get_retriever,
)


logger = logging.getLogger("techcart.api")


@asynccontextmanager
async def lifespan(
    app: FastAPI,
):

    logger.info("Starting TechCart backend...")

    # ─────────────────────────────────────────────
    # 1. MongoDB
    # ─────────────────────────────────────────────

    await connect_to_mongo()

    logger.info(
        "MongoDB connection established."
    )

    # ─────────────────────────────────────────────
    # 2. Load retriever
    # ─────────────────────────────────────────────

    try:
        logger.info(
            "Loading retriever and BGE reranker..."
        )

        retriever = await asyncio.to_thread(
            get_retriever
        )

        logger.info(
            "Retriever loaded successfully."
        )

        # Warm-up:
        # BGE-M3 → Qdrant → BGE reranker
        await asyncio.to_thread(
            retriever.warmup
        )

        logger.info(
            "Retriever warm-up completed."
        )

    except Exception:
        logger.exception(
            "Retriever warm-up failed."
        )

        await close_mongo_connection()

        raise

    # ─────────────────────────────────────────────
    # 3. Load + warm-up LLM
    # ─────────────────────────────────────────────

    try:
        logger.info(
            "Loading LLM provider..."
        )

        llm_provider = get_llm_provider()

        if hasattr(llm_provider, "warm_up"):
            await llm_provider.warm_up()

        logger.info(
            "LLM warm-up completed."
        )

    except Exception:
        logger.exception(
            "LLM warm-up failed."
        )

        await close_mongo_connection()

        raise

    logger.info(
        "TechCart backend is ready."
    )

    yield

    # ─────────────────────────────────────────────
    # SHUTDOWN
    # ─────────────────────────────────────────────

    logger.info(
        "Shutting down TechCart backend..."
    )

    await close_mongo_connection()

    logger.info(
        "TechCart backend stopped."
    )


app = FastAPI(
    title="TechCart API",
    version="1.0.0",
    lifespan=lifespan,
)


# ─────────────────────────────────────────────
# CORS
# ─────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─────────────────────────────────────────────
# ROOT
# ─────────────────────────────────────────────

@app.get("/")
async def root() -> dict[str, str]:
    return {
        "message": "TechCart Backend is running!"
    }


# ─────────────────────────────────────────────
# ROUTES
# ─────────────────────────────────────────────

app.include_router(
    health.router
)

app.include_router(
    chat.router
)

app.include_router(
    conversation.router
)