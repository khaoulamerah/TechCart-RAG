import asyncio
from collections.abc import AsyncIterator
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from fastapi import HTTPException, status

from backend.rag.generator.base import (
    LLMProvider,
    LLMProviderError,
)
from backend.rag.prompt import (
    build_rag_prompt,
)
from backend.rag.retriever.retriever import (
    Retriever,
)
from backend.services.conversation import (
    ConversationService,
)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ChatService:
    """Application service for the TechCart RAG chat."""

    def __init__(
        self,
        conversation_service: ConversationService,
        llm_provider: LLMProvider,
        retriever: Retriever,
    ) -> None:

        self.conversation_service = (
            conversation_service
        )

        self.llm_provider = llm_provider

        self.retriever = retriever

    async def prepare_conversation(
        self,
        message: str,
        session_id: str | None,
        conversation_id: str | None,
    ) -> dict[str, Any]:

        cleaned_message = (
            message or ""
        ).strip()

        if not cleaned_message:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Message cannot be empty.",
            )

        # Existing conversation
        if conversation_id:

            conversation = (
                await self.conversation_service
                .get_conversation(
                    conversation_id
                )
            )

        # Existing/new session
        else:

            session_id = (
                session_id or str(uuid4())
            )

            conversation = (
                await self.conversation_service
                .get_or_create_by_session(
                    session_id
                )
            )

            conversation_id = (
                conversation["id"]
            )

        return {
            "cleaned_message": cleaned_message,
            "conversation_id": conversation_id,
            "session_id": conversation["session_id"],
        }

    async def stream_message(
        self,
        cleaned_message: str,
        conversation_id: str,
        session_id: str,
    ) -> AsyncIterator[dict[str, Any]]:

        # ─────────────────────────────────────────
        # 1. Save user message
        # ─────────────────────────────────────────

        await self.conversation_service.add_message(
            conversation_id,
            {
                "role": "user",
                "content": cleaned_message,
            },
        )

        # Send metadata immediately.
        yield {
            "type": "metadata",
            "conversation_id": conversation_id,
            "session_id": session_id,
        }

        # ─────────────────────────────────────────
        # 2. Retrieve + rerank
        #
        # Run CPU/blocking work outside the
        # FastAPI event loop.
        # ─────────────────────────────────────────

        try:

            retrieved_results = (
                await asyncio.to_thread(
                    self.retriever.retrieve,
                    cleaned_message,
                )
            )

        except Exception:

            yield {
                "type": "error",
                "message": (
                    "I could not retrieve "
                    "relevant information."
                ),
            }

            return

        # ─────────────────────────────────────────
        # 3. Build RAG prompt
        # ─────────────────────────────────────────

        prompt = build_rag_prompt(
            question=cleaned_message,
            results=retrieved_results,
        )

        # ─────────────────────────────────────────
        # 4. Generate response
        # ─────────────────────────────────────────

        full_response: list[str] = []

        try:

            async for chunk in (
                self.llm_provider.generate_stream(
                    prompt
                )
            ):

                if not chunk:
                    continue

                full_response.append(
                    chunk
                )

                yield {
                    "type": "token",
                    "content": chunk,
                }

        except LLMProviderError:

            yield {
                "type": "error",
                "message": (
                    "The AI model is currently "
                    "unavailable."
                ),
            }

            return

        # ─────────────────────────────────────────
        # 5. Validate response
        # ─────────────────────────────────────────

        reply_text = "".join(
            full_response
        ).strip()

        if not reply_text:

            yield {
                "type": "error",
                "message": (
                    "The AI model returned "
                    "an empty response."
                ),
            }

            return

        # ─────────────────────────────────────────
        # 6. Save assistant message
        # ─────────────────────────────────────────

        await self.conversation_service.add_message(
            conversation_id,
            {
                "role": "assistant",
                "content": reply_text,
            },
        )

        # ─────────────────────────────────────────
        # 7. Finish
        # ─────────────────────────────────────────

        yield {
            "type": "done",
            "conversation_id": conversation_id,
            "session_id": session_id,
            "created_at": utcnow().isoformat(),
        }