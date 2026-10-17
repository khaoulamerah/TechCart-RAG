from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from bson import ObjectId


class RAGTraceRepository:
    """
    Repository responsible for storing and retrieving
    RAG execution traces.
    """

    def __init__(self, database):
        self.database = database
        self.collection = database["rag_traces"]

    async def create(
        self,
        trace: dict[str, Any],
    ) -> str:
        """
        Store a RAG trace.

        Returns:
            MongoDB document ID as a string.
        """

        document = dict(trace)

        document.setdefault(
            "created_at",
            datetime.now(timezone.utc),
        )

        result = await self.collection.insert_one(
            document
        )

        return str(result.inserted_id)

    async def get_by_id(
        self,
        trace_id: str,
    ) -> dict[str, Any] | None:
        """
        Retrieve one trace by its MongoDB ID.
        """

        if not ObjectId.is_valid(trace_id):
            return None

        document = await self.collection.find_one(
            {"_id": ObjectId(trace_id)}
        )

        if document is None:
            return None

        document["id"] = str(document.pop("_id"))

        return document

    async def get_by_conversation(
        self,
        conversation_id: str,
    ) -> list[dict[str, Any]]:
        """
        Retrieve all traces belonging to one conversation.
        """

        cursor = self.collection.find(
            {
                "conversation_id": conversation_id,
            }
        ).sort(
            "created_at",
            1,
        )

        documents = await cursor.to_list(
            length=None
        )

        for document in documents:
            document["id"] = str(
                document.pop("_id")
            )

        return documents

    async def get_recent(
        self,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """
        Retrieve the most recent RAG traces.
        """

        limit = max(
            1,
            min(limit, 200),
        )

        cursor = self.collection.find().sort(
            "created_at",
            -1,
        ).limit(limit)

        documents = await cursor.to_list(
            length=limit
        )

        for document in documents:
            document["id"] = str(
                document.pop("_id")
            )

        return documents

    async def create_indexes(self) -> None:
        """
        Create indexes used by the developer interface.
        """

        await self.collection.create_index(
            [
                ("conversation_id", 1),
                ("created_at", 1),
            ]
        )

        await self.collection.create_index(
            [("created_at", -1)]
        )