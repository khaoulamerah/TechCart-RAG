from fastapi import APIRouter, Depends, Query
from motor.motor_asyncio import AsyncIOMotorDatabase

from backend.api.schemas.conversation import (
    ConversationCreate,
    ConversationListResponse,
    ConversationResponse,
    ConversationUpdate,
    MessageCreate,
    MessageResponse,
    MessageUpdate,
)
from backend.database.mongodb import get_database
from backend.repositories.conversation import ConversationRepository
from backend.services.conversation import ConversationService

router = APIRouter(prefix="/conversations", tags=["conversations"])


def get_conversation_service(
    db: AsyncIOMotorDatabase = Depends(get_database),
) -> ConversationService:
    repository = ConversationRepository(db)
    return ConversationService(repository)


# ── Conversation endpoints ───────────────────────────────

@router.post("", response_model=ConversationResponse, status_code=201)
async def create_conversation(
    payload: ConversationCreate,
    service: ConversationService = Depends(get_conversation_service),
):
    return await service.create_conversation(payload.model_dump())


@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: str,
    service: ConversationService = Depends(get_conversation_service),
):
    return await service.get_conversation(conversation_id)


@router.get("", response_model=ConversationListResponse)
async def list_conversations(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    service: ConversationService = Depends(get_conversation_service),
):
    return await service.list_conversations(skip, limit)


@router.put("/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(
    conversation_id: str,
    payload: ConversationUpdate,
    service: ConversationService = Depends(get_conversation_service),
):
    return await service.update_conversation(
        conversation_id, payload.model_dump(exclude_unset=True)
    )


@router.delete("/{conversation_id}", status_code=204)
async def delete_conversation(
    conversation_id: str,
    service: ConversationService = Depends(get_conversation_service),
):
    await service.delete_conversation(conversation_id)


# ── Message endpoints ────────────────────────────────────

@router.post("/{conversation_id}/messages", response_model=ConversationResponse, status_code=201)
async def add_message(
    conversation_id: str,
    payload: MessageCreate,
    service: ConversationService = Depends(get_conversation_service),
):
    return await service.add_message(conversation_id, payload.model_dump())


@router.get("/{conversation_id}/messages", response_model=list[MessageResponse])
async def list_messages(
    conversation_id: str,
    service: ConversationService = Depends(get_conversation_service),
):
    return await service.get_messages(conversation_id)


@router.put("/{conversation_id}/messages/{message_id}", response_model=ConversationResponse)
async def update_message(
    conversation_id: str,
    message_id: str,
    payload: MessageUpdate,
    service: ConversationService = Depends(get_conversation_service),
):
    return await service.update_message(
        conversation_id, message_id, payload.model_dump(exclude_unset=True)
    )


@router.delete("/{conversation_id}/messages/{message_id}", response_model=ConversationResponse)
async def delete_message(
    conversation_id: str,
    message_id: str,
    service: ConversationService = Depends(get_conversation_service),
):
    return await service.delete_message(conversation_id, message_id)