from datetime import datetime, timezone
from uuid import uuid4

from fastapi import HTTPException, status

from backend.rag.generator.base import LLMProvider, LLMProviderError
from backend.services.conversation import ConversationService


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ChatService:
    def __init__(
        self,
        conversation_service: ConversationService,
        llm_provider: LLMProvider,
    ):
        self.conversation_service = conversation_service
        self.llm_provider = llm_provider

    async def send_message(
        self,
        message: str,
        session_id: str | None,
        conversation_id: str | None,
    ) -> dict:
        # ── Validation ───────────────────────────────────
        cleaned_message = (message or "").strip()
        if not cleaned_message:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Message cannot be empty.",
            )

        # ── Resolve the conversation ─────────────────────
        if conversation_id:
            conversation = await self.conversation_service.get_conversation(
                conversation_id
            )
        else:
            session_id = session_id or str(uuid4())
            conversation = await self.conversation_service.get_or_create_by_session(
                session_id
            )
            conversation_id = conversation["id"]

        resolved_session_id = conversation["session_id"]

        # ── Save the user's message ──────────────────────
        await self.conversation_service.add_message(
            conversation_id, {"role": "user", "content": cleaned_message}
        )

        try:
            reply_text = await self.llm_provider.generate(cleaned_message)
        except LLMProviderError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"The AI model is currently unavailable: {exc}",
            ) from exc

        # ── Save the assistant's message ─────────────────
        await self.conversation_service.add_message(
            conversation_id, {"role": "assistant", "content": reply_text}
        )

        return {
            "conversation_id": conversation_id,
            "session_id": resolved_session_id,
            "reply": reply_text,
            "created_at": utcnow(),
            "metadata": {},
        }
