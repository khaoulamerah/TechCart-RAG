
from datetime import datetime, timezone
from typing import Annotated, Any

from bson import ObjectId
from pydantic import BaseModel, BeforeValidator, Field


def validate_object_id(value: Any) -> ObjectId:
    if isinstance(value, ObjectId):
        return value
    if isinstance(value, str) and ObjectId.is_valid(value):
        return ObjectId(value)
    raise ValueError("Invalid ObjectId")


# Lets Pydantic v2 accept/emit ObjectId as a plain string.
PyObjectId = Annotated[ObjectId, BeforeValidator(validate_object_id)]


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class MessageModel(BaseModel):
    """An embedded message subdocument inside a conversation."""

    message_id: str = Field(default_factory=lambda: str(ObjectId()))
    role: str  # "user" | "assistant"
    content: str
    created_at: datetime = Field(default_factory=utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = {"arbitrary_types_allowed": True}


class ConversationModel(BaseModel):
    """A conversation document, as stored in the `conversations` collection."""

    id: PyObjectId = Field(default_factory=ObjectId, alias="_id")
    session_id: str
    user_id: str | None = None
    title: str = "Nouvelle conversation"
    is_guest: bool = True
    messages: list[MessageModel] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str},
    }

