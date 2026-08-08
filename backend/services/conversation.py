from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from bson import ObjectId
from fastapi import HTTPException, status

from backend.repositories.conversation import ConversationRepository

VALID_ROLES = {"user", "assistant"}


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def serialize_conversation(doc: dict[str, Any]) -> dict[str, Any]:
    """Turn a raw Mongo document into a JSON-friendly dict (ObjectId -> str)."""
    return {
        "id": str(doc["_id"]),
        "session_id": doc["session_id"],
        "user_id": doc.get("user_id"),
        "title": doc.get("title", "Nouvelle conversation"),
        "is_guest": doc.get("is_guest", True),
        "messages": doc.get("messages", []),
        "created_at": doc["created_at"],
        "updated_at": doc["updated_at"],
        "metadata": doc.get("metadata", {}),
    }


class ConversationService:
    def __init__(self, repository: ConversationRepository):
        self.repository = repository

    # ── Conversations ────────────────────────────────────

    async def create_conversation(self, payload: dict[str, Any]) -> dict[str, Any]:
        now = utcnow()
        document = {
            "session_id": payload["session_id"],
            "user_id": payload.get("user_id"),
            "title": payload.get("title") or "Nouvelle conversation",
            "is_guest": payload.get("is_guest", True),
            "messages": [],
            "created_at": now,
            "updated_at": now,
            "metadata": payload.get("metadata", {}),
        }
        created = await self.repository.create(document)
        return serialize_conversation(created)

    async def get_conversation(self, conversation_id: str) -> dict[str, Any]:
        doc = await self.repository.get_by_id(conversation_id)
        if doc is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Conversation '{conversation_id}' not found.",
            )
        return serialize_conversation(doc)

    async def get_conversation_by_session(self, session_id: str) -> dict[str, Any]:
        doc = await self.repository.get_by_session_id(session_id)
        if doc is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No conversation for session '{session_id}'.",
            )
        return serialize_conversation(doc)

    async def get_or_create_by_session(self, session_id: str) -> dict[str, Any]:
        """
        Used by the Chat Service: returns the guest's existing
        conversation for this session, or silently creates one.
        Never raises 404 — that's the point of "get or create".
        """
        doc = await self.repository.get_by_session_id(session_id)
        if doc is not None:
            return serialize_conversation(doc)
        return await self.create_conversation(
            {"session_id": session_id, "is_guest": True}
        )

    async def list_conversations(self, skip: int, limit: int) -> dict[str, Any]:
        if skip < 0 or limit <= 0 or limit > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid pagination parameters (0 <= skip, 1 <= limit <= 100).",
            )
        docs, total = await self.repository.list_conversations(skip, limit)
        return {
            "total": total,
            "skip": skip,
            "limit": limit,
            "items": [serialize_conversation(doc) for doc in docs],
        }

    async def update_conversation(
        self, conversation_id: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        # Only accept fields the conversation is actually allowed to edit.
        editable = {
            key: value
            for key, value in payload.items()
            if key in {"title", "user_id", "is_guest", "metadata"} and value is not None
        }
        if not editable:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No editable fields provided.",
            )

        updated = await self.repository.update(conversation_id, editable)
        if updated is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Conversation '{conversation_id}' not found.",
            )
        return serialize_conversation(updated)

    async def delete_conversation(self, conversation_id: str) -> None:
        deleted = await self.repository.delete(conversation_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Conversation '{conversation_id}' not found.",
            )

    # ── Messages ─────────────────────────────────────────

    async def add_message(
        self, conversation_id: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        role = payload.get("role")
        content = payload.get("content", "")

        if role not in VALID_ROLES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid role '{role}'. Must be one of {sorted(VALID_ROLES)}.",
            )
        if not content or not content.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Message content cannot be empty.",
            )

        message = {
            "message_id": str(uuid4()),
            "role": role,
            "content": content,
            "created_at": utcnow(),
            "metadata": payload.get("metadata", {}),
        }

        updated = await self.repository.add_message(conversation_id, message)
        if updated is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Conversation '{conversation_id}' not found.",
            )
        return serialize_conversation(updated)

    async def get_messages(self, conversation_id: str) -> list[dict[str, Any]]:
        messages = await self.repository.get_messages(conversation_id)
        if messages is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Conversation '{conversation_id}' not found.",
            )
        return messages

    async def update_message(
        self, conversation_id: str, message_id: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        editable = {
            key: value
            for key, value in payload.items()
            if key in {"content", "metadata"} and value is not None
        }
        if not editable:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No editable fields provided.",
            )
        if "content" in editable and not editable["content"].strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Message content cannot be empty.",
            )

        updated = await self.repository.update_message(
            conversation_id, message_id, editable
        )
        if updated is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Conversation or message not found "
                f"('{conversation_id}' / '{message_id}').",
            )
        return serialize_conversation(updated)

    async def delete_message(
        self, conversation_id: str, message_id: str
    ) -> dict[str, Any]:
        updated = await self.repository.delete_message(conversation_id, message_id)
        if updated is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Conversation or message not found "
                f"('{conversation_id}' / '{message_id}').",
            )
        return serialize_conversation(updated)