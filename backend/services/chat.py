from collections.abc import AsyncIterator
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from fastapi import HTTPException, status

from backend.rag.generator.base import (
    LLMProvider,
    LLMProviderError,
)
from backend.rag.prompt import build_rag_prompt
from backend.rag.retriever.retriever import Retriever
from backend.services.conversation import ConversationService


def utcnow() -> datetime:
    """Return the current UTC datetime."""
    return datetime.now(timezone.utc)


class ChatService:

    def __init__(
        self,
        conversation_service: ConversationService,
        llm_provider: LLMProvider,
        retriever: Retriever,
    ) -> None:
        self.conversation_service = conversation_service
        self.llm_provider = llm_provider
        self.retriever = retriever

    async def prepare_conversation(
        self,
        message: str,
        session_id: str | None,
        conversation_id: str | None,
    ) -> dict[str, Any]:

        cleaned_message = (message or "").strip()

        if not cleaned_message:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Message cannot be empty.",
            )

        # 1. Existing conversation
        if conversation_id:
            try:
                conversation = (
                    await self.conversation_service.get_conversation(
                        conversation_id
                    )
                )

                return {
                    "cleaned_message": cleaned_message,
                    "conversation_id": conversation["id"],
                    "session_id": conversation["session_id"],
                }

            except HTTPException as exc:
                if exc.status_code != status.HTTP_404_NOT_FOUND:
                    raise

                # The frontend has an obsolete conversation ID.
                # Recover automatically using the session.


        # 2. Existing session or new session
        resolved_session_id = session_id or str(uuid4())

        conversation = (
            await self.conversation_service.get_or_create_by_session(
                resolved_session_id
            )
        )

        return {
            "cleaned_message": cleaned_message,
            "conversation_id": conversation["id"],
            "session_id": conversation["session_id"],
        }

    async def stream_message(
        self,
        message: str,
        session_id: str | None = None,
        conversation_id: str | None = None,
    ) -> AsyncIterator[dict[str, Any]]:

        # 1. Prepare conversation
        conversation_data = await self.prepare_conversation(
            message=message,
            session_id=session_id,
            conversation_id=conversation_id,
        )

        cleaned_message = conversation_data["cleaned_message"]
        conversation_id = conversation_data["conversation_id"]
        session_id = conversation_data["session_id"]


        # 2. Save user message
        await self.conversation_service.add_message(
            conversation_id,
            {
                "role": "user",
                "content": cleaned_message,
            },
        )

        # 3. Retrieve relevant documents
        try:
            retrieved_results = await self.retriever.retrieve(
                cleaned_message
            )

        except Exception:
            yield {
                "type": "error",
                "message": (
                    "The knowledge base is currently unavailable."
                ),
            }
            return


        # 4. Build RAG prompt

        prompt = build_rag_prompt(
            question=cleaned_message,
            results=retrieved_results,
        )


        # 5. Send metadata
        yield {
            "type": "metadata",
            "conversation_id": conversation_id,
            "session_id": session_id,
        }

        # 6. Generate response
        full_response: list[str] = []

        try:
            async for chunk in self.llm_provider.generate_stream(
                prompt
            ):
                if not chunk:
                    continue

                full_response.append(chunk)

                yield {
                    "type": "token",
                    "content": chunk,
                }

        except LLMProviderError:
            yield {
                "type": "error",
                "message": (
                    "The AI model is currently unavailable."
                ),
            }
            return

        # 7. Validate response
        reply_text = "".join(full_response).strip()

        if not reply_text:
            yield {
                "type": "error",
                "message": (
                    "The AI model returned an empty response."
                ),
            }
            return

        # 8. Save assistant message
        await self.conversation_service.add_message(
            conversation_id,
            {
                "role": "assistant",
                "content": reply_text,
            },
        )

        # 9. Finish
        yield {
            "type": "done",
            "conversation_id": conversation_id,
            "session_id": session_id,
            "created_at": utcnow().isoformat(),
        }