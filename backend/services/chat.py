from collections.abc import AsyncIterator
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from fastapi import HTTPException, status

from backend.rag.generator.base import (
    LLMProvider,
    LLMProviderError,
)
from backend.services.conversation import ConversationService


def utcnow() -> datetime:
    """Return the current UTC datetime."""
    return datetime.now(timezone.utc)


class ChatService:

    def __init__(
        self,
        conversation_service: ConversationService,
        llm_provider: LLMProvider,
    ):
        self.conversation_service = conversation_service
        self.llm_provider = llm_provider

    async def stream_message(
        self,
        message: str,
        session_id: str | None,
        conversation_id: str | None,
    ) -> AsyncIterator[dict[str, Any]]:


        cleaned_message = (message or "").strip()

        if not cleaned_message:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Message cannot be empty.",
            )


        if conversation_id:
            conversation = (
                await self.conversation_service.get_conversation(
                    conversation_id
                )
            )
        else:
            session_id = session_id or str(uuid4())

            conversation = (
                await self.conversation_service.get_or_create_by_session(
                    session_id
                )
            )

            conversation_id = conversation["id"]

        resolved_session_id = conversation["session_id"]


        await self.conversation_service.add_message(
            conversation_id,
            {
                "role": "user",
                "content": cleaned_message,
            },
        )


        yield {
            "type": "metadata",
            "conversation_id": conversation_id,
            "session_id": resolved_session_id,
        }

        full_response: list[str] = []

        try:
            async for chunk in self.llm_provider.generate_stream(
                cleaned_message
            ):
                if not chunk:
                    continue

                full_response.append(chunk)

                yield {
                    "type": "token",
                    "content": chunk,
                }

        except LLMProviderError as exc:
            yield {
                "type": "error",
                "message": (
                    "The AI model is currently unavailable."
                ),
            }

            return


        reply_text = "".join(full_response).strip()

        if not reply_text:
            yield {
                "type": "error",
                "message": "The AI model returned an empty response.",
            }

            return


        await self.conversation_service.add_message(
            conversation_id,
            {
                "role": "assistant",
                "content": reply_text,
            },
        )


        yield {
            "type": "done",
            "conversation_id": conversation_id,
            "session_id": resolved_session_id,
            "created_at": utcnow().isoformat(),
        }