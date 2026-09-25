from typing import Any

from FlagEmbedding import FlagReranker

from backend.rag.reranker.base import Reranker


class BGEReranker(Reranker):

    def __init__(
        self,
        model_name: str = "BAAI/bge-reranker-v2-m3",
        use_fp16: bool = False,
    ) -> None:
        self.model_name = model_name

        self.reranker = FlagReranker(
            model_name,
            use_fp16=use_fp16,
        )

    def rerank(
        self,
        query: str,
        documents: list[dict[str, Any]],
        top_k: int,
    ) -> list[dict[str, Any]]:

        if not documents:
            return []

        if top_k <= 0:
            raise ValueError(
                "top_k must be greater than zero."
            )

        pairs = [
            [
                query,
                str(document["payload"]["text"]),
            ]
            for document in documents
        ]

        scores = self.reranker.compute_score(
            pairs,
            normalize=True,
        )

        if isinstance(scores, float):
            scores = [scores]

        reranked_documents = []

        for document, score in zip(
            documents,
            scores,
        ):
            reranked_document = {
                **document,
                "rerank_score": float(score),
            }

            reranked_documents.append(
                reranked_document
            )

        reranked_documents.sort(
            key=lambda item: item["rerank_score"],
            reverse=True,
        )

        return reranked_documents[:top_k]