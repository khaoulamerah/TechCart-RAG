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

logger = logging.getLogger("techcart.api")


@asynccontextmanager
async def lifespan(app: FastAPI):

    logger.info("Starting TechCart backend...")

    # ---------------------------------------------------------
    # MongoDB
    # ---------------------------------------------------------
    try:
        await connect_to_mongo()

        logger.info(
            "MongoDB connection established."
        )

    except Exception:
        logger.exception(
            "MongoDB is unavailable. "
            "Backend will continue without MongoDB."
        )

    logger.info(
        "TechCart backend started."
    )

    yield

    # ---------------------------------------------------------
    # Shutdown
    # ---------------------------------------------------------
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
    return {
        "message": "TechCart Backend is running!"
    }


app.include_router(health.router)
app.include_router(chat.router)
app.include_router(conversation.router)