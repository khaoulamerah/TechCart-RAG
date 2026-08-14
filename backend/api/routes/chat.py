import json
from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse

from backend.api.routes.conversation import (
    get_conversation_service,
)
from backend.api.schemas.chat import ChatMessageRequest
from backend.api.schemas.conversation import (
    ConversationListResponse,
    ConversationResponse,
)
from backend.rag.generator.base import LLMProvider
from backend.rag.generator.factory import get_llm_provider
from backend.services.chat import ChatService
from backend.services.conversation import ConversationService


router = APIRouter(
    prefix="/chat",
    tags=["chat"],
)


def get_chat_service(
    conversation_service: ConversationService = Depends(
        get_conversation_service
    ),
    llm_provider: LLMProvider = Depends(
        get_llm_provider
    ),
) -> ChatService:
    return ChatService(
        conversation_service=conversation_service,
        llm_provider=llm_provider,
    )


def format_sse(
    event: str,
    data: dict,
) -> str:


    return (
        f"event: {event}\n"
        f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
    )


@router.post("")
async def send_chat_message(
    payload: ChatMessageRequest,
    chat_service: ChatService = Depends(
        get_chat_service
    ),
):
    resolved = await chat_service.prepare_conversation(
        message=payload.message,
        session_id=payload.session_id,
        conversation_id=payload.conversation_id,
    )

    async def event_generator() -> AsyncIterator[str]:
        try:
            async for event in chat_service.stream_message(
                cleaned_message=resolved["cleaned_message"],
                conversation_id=resolved["conversation_id"],
                session_id=resolved["session_id"],
            ):
                event_type = event.get(
                    "type",
                    "message",
                )

                yield format_sse(
                    event=event_type,
                    data=event,
                )

        except Exception:
            # The HTTP response has already started.
            # Therefore, communicate the error through SSE.
            yield format_sse(
                event="error",
                data={
                    "message": (
                        "An unexpected error occurred "
                        "while generating the response."
                    )
                },
            )

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get(
    "/conversations/{conversation_id}",
    response_model=ConversationResponse,
)
async def get_chat_conversation(
    conversation_id: str,
    service: ConversationService = Depends(
        get_conversation_service
    ),
):
    return await service.get_conversation(
        conversation_id
    )


@router.get(
    "/conversations",
    response_model=ConversationListResponse,
)
async def list_chat_conversations(
    skip: int = Query(
        default=0,
        ge=0,
    ),
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
    service: ConversationService = Depends(
        get_conversation_service
    ),
):
    return await service.list_conversations(
        skip,
        limit,
    )


@router.delete(
    "/conversations/{conversation_id}",
    status_code=204,
)
async def delete_chat_conversation(
    conversation_id: str,
    service: ConversationService = Depends(
        get_conversation_service
    ),
):
    await service.delete_conversation(
        conversation_id
    )