import logging

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from backend.config.settings import settings

logger = logging.getLogger(__name__)


class MongoDB:
    client: AsyncIOMotorClient | None = None
    db: AsyncIOMotorDatabase | None = None


mongodb = MongoDB()


async def connect_to_mongo() -> None:
    # Open the Mongo connection. Call once on FastAPI startup.
    logger.info("Connecting to MongoDB at %s", settings.MONGODB_URL.split("@")[-1])
    mongodb.client = AsyncIOMotorClient(settings.MONGODB_URL)
    mongodb.db = mongodb.client[settings.MONGODB_DB]

    # Fail fast if the connection is actually broken, instead of
    # discovering it on the first request.
    await mongodb.client.admin.command("ping")
    logger.info("MongoDB connection established.")

    await create_indexes()


async def close_mongo_connection() -> None:
    # Close the Mongo connection. Call once on FastAPI shutdown.
    if mongodb.client:
        mongodb.client.close()
        logger.info("MongoDB connection closed.")


async def create_indexes() -> None:
    conversations = mongodb.db["conversations"]
    await conversations.create_index("session_id", unique=True)
    await conversations.create_index("user_id")
    await conversations.create_index("created_at")
    logger.info("MongoDB indexes ensured on 'conversations'.")


def get_database() -> AsyncIOMotorDatabase:
    if mongodb.db is None:
        raise RuntimeError("MongoDB has not been initialized. Did startup run?")
    return mongodb.db
