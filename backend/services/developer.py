from __future__ import annotations

from typing import Any


class DeveloperService:
    """Business logic for the developer / observability interface."""

    def __init__(self, conversation_repository, rag_trace_repository):
        self.conversation_repository = conversation_repository
        self.rag_trace_repository = rag_trace_repository

    @staticmethod
    def _conversation_id(document: dict[str, Any]) -> str:
        value = document.get("_id", document.get("id", ""))
        return str(value)

    @classmethod
    def _serialize_conversation(
        cls,
        document: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "id": cls._conversation_id(document),
            "session_id": document.get("session_id"),
            "title": document.get("title", "Nouvelle conversation"),
            "messages": document.get("messages", []),
            "created_at": document.get("created_at"),
            "updated_at": document.get("updated_at"),
        }

    async def list_conversations(
        self,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        conversations = await self.conversation_repository.get_recent(
            limit=limit
        )

        return [
            {
                "id": self._conversation_id(conversation),
                "session_id": conversation.get("session_id"),
                "title": conversation.get(
                    "title",
                    "Nouvelle conversation",
                ),
                "message_count": len(
                    conversation.get("messages", [])
                ),
                "created_at": conversation.get("created_at"),
                "updated_at": conversation.get("updated_at"),
            }
            for conversation in conversations
        ]

    async def get_conversation(
        self,
        conversation_id: str,
    ) -> dict[str, Any] | None:
        conversation = await self.conversation_repository.get_by_id(
            conversation_id
        )

        if conversation is None:
            return None

        return self._serialize_conversation(conversation)

    async def get_trace(
        self,
        trace_id: str,
    ) -> dict[str, Any] | None:
        return await self.rag_trace_repository.get_by_id(trace_id)

    async def get_conversation_traces(
        self,
        conversation_id: str,
    ) -> list[dict[str, Any]]:
        return await self.rag_trace_repository.get_by_conversation(
            conversation_id
        )

    async def get_recent_traces(
        self,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        return await self.rag_trace_repository.get_recent(limit)
