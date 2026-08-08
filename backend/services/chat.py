from datetime import datetime, timezone
from uuid import uuid4

from fastapi import HTTPException, status

from backend.services.conversation import ConversationService

FIXED_ASSISTANT_REPLY = "this is just a testing message of devlopment"


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ChatService:
    def __init__(self, conversation_service: ConversationService):
        self.conversation_service = conversation_service

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
            # Explicit conversation_id: must exist, or it's a 404 —
            # this is what "invalid conversation ID" validation means.
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

        # ── Generate the fixed response (no LLM in Task 2) ──
        reply_text = FIXED_ASSISTANT_REPLY

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