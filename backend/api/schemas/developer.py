from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class RetrievalDocument(BaseModel):
    chunk_id: str
    document: str | None = None
    text: str
    vector_score: float | None = None
    bm25_score: float | None = None
    hybrid_score: float | None = None


class RetrievalTrace(BaseModel):
    embedding_model: str | None = None
    top_k: int = 0
    latency_ms: float = 0.0
    embedding_latency_ms: float | None = None
    vector_search_latency_ms: float | None = None
    documents: list[RetrievalDocument] = Field(default_factory=list)


class RerankedDocument(BaseModel):
    chunk_id: str
    document: str | None = None
    text: str
    original_score: float | None = None
    rerank_score: float | None = None


class RerankingTrace(BaseModel):
    model: str | None = None
    input_count: int = 0
    output_count: int = 0
    latency_ms: float = 0.0
    documents: list[RerankedDocument] = Field(
        default_factory=list
    )


class LLMTrace(BaseModel):
    model: str | None = None
    provider: str | None = None
    time_to_first_token_ms: float | None = None
    latency_ms: float = 0.0
    response: str = ""
    context: list[str] = Field(default_factory=list)


class RAGTraceResponse(BaseModel):
    id: str
    conversation_id: str
    message_id: str | None = None

    question: str

    created_at: datetime

    retrieval: RetrievalTrace | None = None
    reranking: RerankingTrace | None = None
    llm: LLMTrace | None = None

    context: list[str] = Field(default_factory=list)

    prompt: str | None = None

    total_latency_ms: float = 0.0

    status: str = "success"
    error: str | None = None


class DeveloperConversationSummary(BaseModel):
    id: str
    session_id: str | None = None
    title: str | None = None
    message_count: int = 0
    created_at: datetime | None = None
    updated_at: datetime | None = None


class DeveloperConversationResponse(BaseModel):
    id: str
    session_id: str | None = None
    title: str | None = None
    messages: list[dict[str, Any]] = Field(
        default_factory=list
    )
    created_at: datetime | None = None
    updated_at: datetime | None = None