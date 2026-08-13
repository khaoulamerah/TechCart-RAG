from datetime import datetime, timezone
from typing import Any

from bson import ObjectId
from bson.errors import InvalidId
from motor.motor_asyncio import AsyncIOMotorDatabase


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ConversationRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db["conversations"]

    @staticmethod
    def _to_object_id(conversation_id: str) -> ObjectId | None:
        try:
            return ObjectId(conversation_id)
        except (InvalidId, TypeError):
            return None

    # ── Conversation CRUD ────────────────────────────────

    async def create(self, document: dict[str, Any]) -> dict[str, Any]:
        result = await self.collection.insert_one(document)
        return await self.collection.find_one({"_id": result.inserted_id})

    async def get_by_id(self, conversation_id: str) -> dict[str, Any] | None:
        oid = self._to_object_id(conversation_id)
        if oid is None:
            return None
        return await self.collection.find_one({"_id": oid})

    async def get_by_session_id(self, session_id: str) -> dict[str, Any] | None:
        return await self.collection.find_one({"session_id": session_id})

    async def get_by_user_id(self, user_id: str) -> list[dict[str, Any]]:
        cursor = self.collection.find({"user_id": user_id}).sort("created_at", -1)
        return await cursor.to_list(length=None)

    async def list_conversations(
        self, skip: int = 0, limit: int = 20
    ) -> tuple[list[dict[str, Any]], int]:
        total = await self.collection.count_documents({})
        cursor = self.collection.find({}).sort("created_at", -1).skip(skip).limit(limit)
        items = await cursor.to_list(length=limit)
        return items, total

    async def update(
        self, conversation_id: str, updates: dict[str, Any]
    ) -> dict[str, Any] | None:
        oid = self._to_object_id(conversation_id)
        if oid is None:
            return None
        updates["updated_at"] = utcnow()
        await self.collection.update_one({"_id": oid}, {"$set": updates})
        return await self.collection.find_one({"_id": oid})

    async def delete(self, conversation_id: str) -> bool:
        oid = self._to_object_id(conversation_id)
        if oid is None:
            return False
        result = await self.collection.delete_one({"_id": oid})
        return result.deleted_count == 1

    # ── Embedded message operations ─────────────────────

    async def add_message(
        self, conversation_id: str, message: dict[str, Any]
    ) -> dict[str, Any] | None:
        oid = self._to_object_id(conversation_id)
        if oid is None:
            return None
        await self.collection.update_one(
            {"_id": oid},
            {
                "$push": {"messages": message},
                "$set": {"updated_at": utcnow()},
            },
        )
        return await self.collection.find_one({"_id": oid})

    async def get_messages(self, conversation_id: str) -> list[dict[str, Any]] | None:
        doc = await self.get_by_id(conversation_id)
        if doc is None:
            return None
        return doc.get("messages", [])

    async def update_message(
        self, conversation_id: str, message_id: str, updates: dict[str, Any]
    ) -> dict[str, Any] | None:
        oid = self._to_object_id(conversation_id)
        if oid is None:
            return None

        set_fields = {f"messages.$.{key}": value for key, value in updates.items()}
        set_fields["updated_at"] = utcnow()

        result = await self.collection.update_one(
            {"_id": oid, "messages.message_id": message_id},
            {"$set": set_fields},
        )
        if result.matched_count == 0:
            return None
        return await self.collection.find_one({"_id": oid})

    async def delete_message(
        self, conversation_id: str, message_id: str
    ) -> dict[str, Any] | None:
        oid = self._to_object_id(conversation_id)
        if oid is None:
            return None

        result = await self.collection.update_one(
            {"_id": oid, "messages.message_id": message_id},
            {
                "$pull": {"messages": {"message_id": message_id}},
                "$set": {"updated_at": utcnow()},
            },
        )
        if result.matched_count == 0:
            return None
        return await self.collection.find_one({"_id": oid})
