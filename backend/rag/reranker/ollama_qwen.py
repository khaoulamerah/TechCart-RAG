from __future__ import annotations

import logging
import math
import threading
from typing import Any

import httpx

from backend.rag.reranker.base import Reranker

logger = logging.getLogger("techcart.reranker.ollama")

DEFAULT_INSTRUCTION = (
    "Given a web search query, retrieve relevant passages that answer the query"
)
SYSTEM_PROMPT = (
    "<|im_start|>system\n"
    'Judge whether the Document meets the requirements based on the Query and '
    'the Instruct provided. Note that the answer can only be "yes" or "no".'
    "<|im_end|>\n"
    "<|im_start|>user\n"
)
ASSISTANT_SUFFIX = (
    "<|im_end|>\n"
    "<|im_start|>assistant\n"
    "<think>\n\n</think>\n\n"
)


class OllamaQwenReranker(Reranker):

    def __init__(
        self,
        model_name: str,
        base_url: str = "http://ollama:11434",
        timeout_seconds: float = 30.0,
        top_logprobs: int = 20,
        instruction: str = DEFAULT_INSTRUCTION,
        max_document_chars: int = 12_000,
    ) -> None:
        if not model_name or not model_name.strip():
            raise ValueError("model_name cannot be empty.")
        if not base_url or not base_url.strip():
            raise ValueError("base_url cannot be empty.")
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be greater than zero.")
        if not 1 <= top_logprobs <= 20:
            raise ValueError("top_logprobs must be between 1 and 20.")
        if not instruction or not instruction.strip():
            raise ValueError("instruction cannot be empty.")
        if max_document_chars <= 0:
            raise ValueError("max_document_chars must be greater than zero.")

        self.model_name = model_name.strip()
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = float(timeout_seconds)
        self.top_logprobs = top_logprobs
        self.instruction = instruction.strip()
        self.max_document_chars = max_document_chars
        self._warned_binary_fallback = False
        self._request_lock = threading.Lock()
        self._client = httpx.Client(
            timeout=httpx.Timeout(
                timeout=self.timeout_seconds,
                connect=min(10.0, self.timeout_seconds),
            ),
        )

    @staticmethod
    def _normalize_token(token: Any) -> str:
        return str(token or "").strip().lower()

    def _build_prompt(self, query: str, document: str) -> str:
        """Build the raw Qwen3-Reranker prompt expected by its scoring recipe."""
        truncated_document = document[: self.max_document_chars]
        pair = (
            f"<Instruct>: {self.instruction}\n\n"
            f"<Query>: {query.strip()}\n\n"
            f"<Document>: {truncated_document}"
        )
        return f"{SYSTEM_PROMPT}{pair}{ASSISTANT_SUFFIX}"

    @staticmethod
    def _label_from_text(text: Any) -> str | None:
        """Return a strict yes/no label from the first generated token/text."""
        normalized = str(text or "").strip().lower()
        first_word = normalized.split(maxsplit=1)[0] if normalized else ""
        first_word = first_word.strip(".,:;!?\"'`()[]{}")
        if first_word == "yes":
            return "yes"
        if first_word == "no":
            return "no"
        return None

    def _score_from_response(self, payload: dict[str, Any]) -> float:
        logprob_entries = payload.get("logprobs") or []
        top_token_logprobs: dict[str, float] = {}
        selected_logprob: float | None = None
        selected_token: str | None = None

        if logprob_entries and isinstance(logprob_entries[0], dict):
            first_entry = logprob_entries[0]
            selected_token = self._normalize_token(first_entry.get("token"))
            raw_selected_logprob = first_entry.get("logprob")
            if isinstance(raw_selected_logprob, (int, float)):
                selected_logprob = float(raw_selected_logprob)

            for candidate in first_entry.get("top_logprobs") or []:
                if not isinstance(candidate, dict):
                    continue
                token = self._normalize_token(candidate.get("token"))
                logprob = candidate.get("logprob")
                if token in {"yes", "no"} and isinstance(logprob, (int, float)):
                    top_token_logprobs[token] = float(logprob)

        # Some Ollama versions expose the selected token in the top-level
        # logprobs array but omit it from top_logprobs. Preserve that value.
        if (
            selected_token in {"yes", "no"}
            and selected_logprob is not None
            and selected_token not in top_token_logprobs
        ):
            top_token_logprobs[selected_token] = selected_logprob

        if not top_token_logprobs:
            label = self._label_from_text(payload.get("response", ""))
            if label is None:
                raise RuntimeError(
                    "Ollama did not return usable yes/no log probabilities or "
                    "a yes/no label. Verify the installed model and Ollama "
                    "/api/generate logprobs support."
                )
            if not self._warned_binary_fallback:
                logger.warning(
                    "Ollama model '%s' returned no usable yes/no logprobs; "
                    "using binary relevance scores for compatibility.",
                    self.model_name,
                )
                self._warned_binary_fallback = True
            return 1.0 if label == "yes" else 0.0

        # This matches the official Qwen3-Reranker recipe: missing yes/no
        # candidates are assigned -10 before a two-class softmax.
        yes_logprob = top_token_logprobs.get("yes", -10.0)
        no_logprob = top_token_logprobs.get("no", -10.0)
        difference = yes_logprob - no_logprob

        # Numerically stable sigmoid(difference).
        if difference >= 0:
            return 1.0 / (1.0 + math.exp(-difference))
        exp_difference = math.exp(difference)
        return exp_difference / (1.0 + exp_difference)

    def _score_pair(self, query: str, document: str) -> float:
        prompt = self._build_prompt(query, document)
        try:
            response = self._client.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "raw": True,
                    "stream": False,
                    "keep_alive": "10m",
                    "logprobs": True,
                    "top_logprobs": self.top_logprobs,
                    "options": {
                        "temperature": 0,
                        "num_predict": 1,
                        "num_ctx": 8192,
                    },
                },
            )
            response.raise_for_status()
            payload = response.json()
            return self._score_from_response(payload)
        except httpx.HTTPError as exc:
            raise RuntimeError(
                f"Ollama reranker request failed for model "
                f"'{self.model_name}' at {self.base_url}: {exc}"
            ) from exc
        except ValueError as exc:
            # Includes invalid JSON from the Ollama response.
            raise RuntimeError(
                f"Ollama reranker returned an invalid response for "
                f"'{self.model_name}'."
            ) from exc

    def warm_up(self) -> None:
        logger.info("Warming up Ollama reranker '%s'...", self.model_name)
        with self._request_lock:
            self._score_pair(
                "What is the store return policy?",
                "Customers can return eligible products according to the store's return policy.",
            )
        logger.info("Ollama reranker '%s' is ready.", self.model_name)

    def rerank(
        self,
        query: str,
        documents: list[dict[str, Any]],
        top_k: int,
    ) -> list[dict[str, Any]]:
        if not query or not query.strip():
            raise ValueError("Query cannot be empty.")
        if top_k <= 0:
            raise ValueError("top_k must be greater than zero.")
        if not documents:
            return []

        scored_documents: list[dict[str, Any]] = []
        # Ollama may have limited parallel slots on a local machine. Keep one
        # reranking batch sequential to avoid flooding its queue with requests.
        with self._request_lock:
            for document in documents:
                payload = document.get("payload") or {}
                text = str(payload.get("text", "")).strip()
                if text:
                    score = self._score_pair(query.strip(), text)
                else:
                    score = 0.0
                scored_documents.append(
                    {
                        **document,
                        "rerank_score": float(score),
                    }
                )

        scored_documents.sort(
            key=lambda item: item["rerank_score"],
            reverse=True,
        )
        return scored_documents[:top_k]
