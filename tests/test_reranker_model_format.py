from services.reranker.model import Qwen3Reranker


def test_qwen_pair_format_uses_instruction_query_document() -> None:
    model = Qwen3Reranker(device="cpu")
    formatted = model._format_pair(
        "What is the return policy?",
        "Eligible products can be returned within 30 days.",
    )
    assert formatted.startswith("<Instruct>: Given a web search query")
    assert "\n<Query>: What is the return policy?" in formatted
    assert "\n<Document>: Eligible products can be returned within 30 days." in formatted
