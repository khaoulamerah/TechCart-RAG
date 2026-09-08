from pydantic import BaseModel, Field


class ChatMessageRequest(BaseModel):

    message: str = Field(
        min_length=1,
        max_length=4000,
    )

    session_id: str | None = None

    conversation_id: str | None = None