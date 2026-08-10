from fastapi import APIRouter, Depends, Query
from motor.motor_asyncio import AsyncIOMotorDatabase

from backend.api.routes.conversation import get_conversation_service
from backend.api.schemas.chat import ChatMessageRequest, ChatMessageResponse
from backend.api.schemas.conversation import (
    ConversationListResponse,
    ConversationResponse,
)
from backend.rag.generator.base import LLMProvider
from backend.rag.generator.factory import get_llm_provider
from backend.services.chat import ChatService
from backend.services.conversation import ConversationService

router = APIRouter(prefix="/chat", tags=["chat"])


def get_chat_service(
    conversation_service: ConversationService = Depends(get_conversation_service),
    llm_provider: LLMProvider = Depends(get_llm_provider),
) -> ChatService:
    return ChatService(conversation_service, llm_provider)


@router.post("", response_model=ChatMessageResponse)
async def send_chat_message(
    payload: ChatMessageRequest,
    chat_service: ChatService = Depends(get_chat_service),
):
    return await chat_service.send_message(
        message=payload.message,
        session_id=payload.session_id,
        conversation_id=payload.conversation_id,
    )


@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_chat_conversation(
    conversation_id: str,
    service: ConversationService = Depends(get_conversation_service),
):
    return await service.get_conversation(conversation_id)


@router.get("/conversations", response_model=ConversationListResponse)
async def list_chat_conversations(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    service: ConversationService = Depends(get_conversation_service),
):
    return await service.list_conversations(skip, limit)


@router.delete("/conversations/{conversation_id}", status_code=204)
async def delete_chat_conversation(
    conversation_id: str,
    service: ConversationService = Depends(get_conversation_service),
):
    await service.delete_conversation(conversation_id)