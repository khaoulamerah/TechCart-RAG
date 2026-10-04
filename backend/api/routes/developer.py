from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from motor.motor_asyncio import AsyncIOMotorDatabase

from backend.api.schemas.developer import (
    DeveloperConversationResponse,
    DeveloperConversationSummary,
    RAGTraceResponse,
)
from backend.database.mongodb import get_database
from backend.repositories.conversation import ConversationRepository
from backend.repositories.rag_trace import RAGTraceRepository
from backend.services.developer import DeveloperService


router = APIRouter(
    prefix="/developer",
    tags=["developer"],
)


def get_developer_service(
    database: AsyncIOMotorDatabase = Depends(get_database),
) -> DeveloperService:
    return DeveloperService(
        conversation_repository=ConversationRepository(database),
        rag_trace_repository=RAGTraceRepository(database),
    )


@router.get(
    "/conversations",
    response_model=list[DeveloperConversationSummary],
)
async def list_conversations(
    limit: int = Query(default=50, ge=1, le=200),
    service: DeveloperService = Depends(get_developer_service),
):
    return await service.list_conversations(limit=limit)


@router.get(
    "/conversations/{conversation_id}",
    response_model=DeveloperConversationResponse,
)
async def get_conversation(
    conversation_id: str,
    service: DeveloperService = Depends(get_developer_service),
):
    conversation = await service.get_conversation(conversation_id)

    if conversation is None:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found.",
        )

    return conversation


@router.get(
    "/conversations/{conversation_id}/traces",
    response_model=list[RAGTraceResponse],
)
async def get_conversation_traces(
    conversation_id: str,
    service: DeveloperService = Depends(get_developer_service),
):
    return await service.get_conversation_traces(conversation_id)


@router.get(
    "/traces/{trace_id}",
    response_model=RAGTraceResponse,
)
async def get_trace(
    trace_id: str,
    service: DeveloperService = Depends(get_developer_service),
):
    trace = await service.get_trace(trace_id)

    if trace is None:
        raise HTTPException(
            status_code=404,
            detail="RAG trace not found.",
        )

    return trace


@router.get(
    "/traces",
    response_model=list[RAGTraceResponse],
)
async def get_recent_traces(
    limit: int = Query(default=50, ge=1, le=200),
    service: DeveloperService = Depends(get_developer_service),
):
    return await service.get_recent_traces(limit=limit)
