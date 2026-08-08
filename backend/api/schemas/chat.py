from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ChatMessageRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    session_id: str | None = None
    conversation_id: str | None = None


class ChatMessageResponse(BaseModel):
    conversation_id: str
    session_id: str
    reply: str
    created_at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)