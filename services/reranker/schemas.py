from typing import Any

from pydantic import BaseModel, Field, field_validator


class RerankRequest(BaseModel):
    query: str = Field(min_length=1)
    documents: list[dict[str, Any]]
    top_k: int = Field(ge=1)

    @field_validator("query")
    @classmethod
    def query_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("query cannot be blank")
        return value.strip()


class RerankResponse(BaseModel):
    documents: list[dict[str, Any]]
    model: str
