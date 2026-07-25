from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes import chat, conversation, health
from backend.database.mongodb import close_mongo_connection, connect_to_mongo


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: open the MongoDB connection once for the app's lifetime.
    await connect_to_mongo()
    yield
    # Shutdown: close it cleanly.
    await close_mongo_connection()


app = FastAPI(
    title="TechCart API",
    version="1.0.0",
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "TechCart Backend is running!"}


app.include_router(health.router)
app.include_router(chat.router)
app.include_router(conversation.router)