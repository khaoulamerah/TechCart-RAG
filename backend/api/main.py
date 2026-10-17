import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes import chat, conversation, developer, health
from backend.database.mongodb import close_mongo_connection, connect_to_mongo
from backend.rag.generator.factory import get_llm_provider
from backend.rag.retriever.factory import get_retriever

logger = logging.getLogger("techcart.api")


async def warmup_llm() -> None:
    try:
        provider = get_llm_provider()
        await provider.warm_up()
        logger.info("LLM warm-up completed successfully.")
    except Exception:
        logger.exception("LLM warm-up failed. Backend will continue running.")


async def warmup_reranker() -> None:
    try:
        retriever = get_retriever()

        if retriever.reranker is None:
            logger.info("Reranker is disabled; skipping warm-up.")
            return

        await asyncio.to_thread(retriever.reranker.warm_up)
        logger.info("Reranker warm-up completed successfully.")
    except Exception:
        logger.exception("Reranker warm-up failed. Backend will continue running.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting TechCart backend...")

    try:
        await connect_to_mongo()
        logger.info("MongoDB connection established.")
    except Exception:
        logger.exception(
            "MongoDB is unavailable. Backend will continue without MongoDB."
        )

    async def warmup_models_in_sequence() -> None:
        # Warm up the chat model and check the separately hosted reranker in
        # sequence to keep startup logs and resource usage easier to diagnose.
        await warmup_llm()
        await warmup_reranker()

    warmup_task = asyncio.create_task(warmup_models_in_sequence())

    logger.info("TechCart backend started.")

    try:
        yield
    finally:
        logger.info("Shutting down TechCart backend...")

        if not warmup_task.done():
            warmup_task.cancel()

        await asyncio.gather(warmup_task, return_exceptions=True)

        try:
            retriever = get_retriever()
            close_reranker = getattr(retriever.reranker, "close", None)
            if callable(close_reranker):
                await asyncio.to_thread(close_reranker)
        except Exception:
            logger.exception("Failed to close reranker client cleanly.")

        await close_mongo_connection()
        logger.info("TechCart backend stopped.")


app = FastAPI(
    title="TechCart API",
    version="1.0.0",
    lifespan=lifespan,
)

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


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "TechCart Backend is running!"}


app.include_router(health.router)
app.include_router(chat.router)
app.include_router(conversation.router)
app.include_router(developer.router)
