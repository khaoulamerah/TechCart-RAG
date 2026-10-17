"""Validated request and response contracts for the reranker API."""

from pydantic import BaseModel, Field


class DocumentCandidate(BaseModel):
    """One text candidate and its index in the caller's original list."""

    index: int = Field(ge=0)
    text: str = Field(min_length=1, max_length=12000)


class RerankRequest(BaseModel):
    """Documents to rank for a single user query."""

    query: str = Field(min_length=1, max_length=4000)
    documents: list[DocumentCandidate] = Field(max_length=50)
    top_k: int = Field(default=5, ge=1, le=50)


class RankedDocument(BaseModel):
    """One document index and its relevance score."""

    index: int = Field(ge=0)
    score: float


class RerankResponse(BaseModel):
    """Reranked indexes ordered from most to least relevant."""

    results: list[RankedDocument]
