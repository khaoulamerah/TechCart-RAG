"""
Minimal endpoint so the frontend can talk to something today.
This bypasses the RAG pipeline (SQL/vector retrieval, reranking) —
it's here to unblock the UI and validate the Ollama connection.
Replace the body with a call into backend/rag/generator/ once
retrieval is wired up.
"""
import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.config.settings import settings

router = APIRouter(tags=["chat"])


class ChatRequest(BaseModel):
    question: str
    session_id: str
    conversation_id: str | None = None


class ChatResponse(BaseModel):
    answer: str


@router.post("/api/chat", response_model=ChatResponse)
async def chat(payload: ChatRequest):
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{settings.OLLAMA_BASE_URL}/api/generate",
                json={
                    "model": settings.LLM_MODEL,
                    "prompt": payload.question,
                    "stream": False,
                },
            )
            response.raise_for_status()
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Could not reach Ollama at {settings.OLLAMA_BASE_URL}: {exc}",
        ) from exc

    data = response.json()
    return ChatResponse(answer=data.get("response", ""))