import pytest
from pydantic import ValidationError

from services.reranker.schemas import DocumentCandidate, RerankRequest


def test_rerank_request_contract() -> None:
    request = RerankRequest(
        query="What is the return policy?",
        documents=[
            DocumentCandidate(index=4, text="Eligible returns are accepted within 30 days."),
            DocumentCandidate(index=8, text="GPU specifications and clock speeds."),
        ],
        top_k=2,
    )
    assert request.top_k == 2
    assert [doc.index for doc in request.documents] == [4, 8]


def test_invalid_rerank_input_is_rejected() -> None:
    with pytest.raises(ValidationError):
        RerankRequest(query="", documents=[], top_k=1)
    with pytest.raises(ValidationError):
        DocumentCandidate(index=-1, text="document")
