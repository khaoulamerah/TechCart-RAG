from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

# ── Messages ──────────────────────────────────────────────


class MessageCreate(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)


class MessageUpdate(BaseModel):
    content: str | None = Field(default=None, min_length=1)
    metadata: dict[str, Any] | None = None


class MessageResponse(BaseModel):
    message_id: str
    role: str
    content: str
    created_at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)


# ── Conversations ─────────────────────────────────────────


class ConversationCreate(BaseModel):
    session_id: str
    user_id: str | None = None
    title: str = "Nouvelle conversation"
    is_guest: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)


class ConversationUpdate(BaseModel):
    title: str | None = None
    user_id: str | None = None
    is_guest: bool | None = None
    metadata: dict[str, Any] | None = None


class ConversationResponse(BaseModel):
    id: str
    session_id: str
    user_id: str | None
    title: str
    is_guest: bool
    messages: list[MessageResponse]
    created_at: datetime
    updated_at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)


class ConversationListResponse(BaseModel):
    total: int
    skip: int
    limit: int
    items: list[ConversationResponse]
