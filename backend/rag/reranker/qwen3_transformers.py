from __future__ import annotations

import logging
import threading
from typing import Any

from backend.rag.reranker.base import Reranker

logger = logging.getLogger("techcart.reranker.qwen3_transformers")

DEFAULT_INSTRUCTION = (
    "Given a web search query, retrieve relevant passages that answer the query"
)

SYSTEM_PREFIX = (
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


class Qwen3TransformersReranker(Reranker):
    """Run Qwen3-Reranker with Transformers and score yes/no logits directly.

    Unlike the previous Ollama adapter, this class does not generate a text
    response and does not depend on Ollama returning log-probabilities. It
    runs a forward pass and computes softmax over the model logits for the
    ``no`` and ``yes`` tokens, following the official Qwen3-Reranker recipe.

    The default device is ``auto``: CUDA is used only when PyTorch reports it
    is available; otherwise inference runs on CPU. CPU inference is slower but
    does not require an NVIDIA GPU.
    """

    def __init__(
        self,
        model_name: str = "Qwen/Qwen3-Reranker-0.6B",
        device: str = "auto",
        max_length: int = 2048,
        instruction: str = DEFAULT_INSTRUCTION,
        max_document_chars: int = 12000,
    ) -> None:
        if not model_name or not model_name.strip():
            raise ValueError("model_name cannot be empty.")
        if device not in {"auto", "cpu", "cuda"}:
            raise ValueError("device must be one of: auto, cpu, cuda.")
        if max_length < 128:
            raise ValueError("max_length must be at least 128 tokens.")
        if not instruction or not instruction.strip():
            raise ValueError("instruction cannot be empty.")
        if max_document_chars <= 0:
            raise ValueError("max_document_chars must be greater than zero.")

        self.model_name = model_name.strip()
        self.device_preference = device
        self.max_length = int(max_length)
        self.instruction = instruction.strip()
        self.max_document_chars = int(max_document_chars)

        self._tokenizer: Any | None = None
        self._model: Any | None = None
        self._torch: Any | None = None
        self._device: str | None = None
        self._prefix_tokens: list[int] = []
        self._suffix_tokens: list[int] = []
        self._token_true_id: int | None = None
        self._token_false_id: int | None = None
        self._load_lock = threading.Lock()
        self._inference_lock = threading.Lock()

    def _ensure_model_loaded(self) -> None:
        """Load the tokenizer and model once, on first use."""
        if self._model is not None and self._tokenizer is not None:
            return

        with self._load_lock:
            if self._model is not None and self._tokenizer is not None:
                return

            # Import lazily so the backend can start even if the reranker is
            # disabled, without loading PyTorch/Transformers unnecessarily.
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer

            if self.device_preference == "auto":
                device = "cuda" if torch.cuda.is_available() else "cpu"
            else:
                device = self.device_preference

            if device == "cuda" and not torch.cuda.is_available():
                raise RuntimeError(
                    "RERANKER_DEVICE=cuda was configured, but CUDA is not "
                    "available in this container. Set RERANKER_DEVICE=cpu "
                    "or configure Docker GPU access."
                )

            dtype = torch.float16 if device == "cuda" else torch.float32
            logger.info(
                "Loading Qwen3 reranker '%s' on %s (dtype=%s)...",
                self.model_name,
                device,
                dtype,
            )

            tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                padding_side="left",
            )
            model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                torch_dtype=dtype,
            )
            model.to(device)
            model.eval()

            true_ids = tokenizer.encode("yes", add_special_tokens=False)
            false_ids = tokenizer.encode("no", add_special_tokens=False)
            if len(true_ids) != 1 or len(false_ids) != 1:
                raise RuntimeError(
                    "The tokenizer must encode 'yes' and 'no' as one token "
                    "each; unable to initialize Qwen3 reranker scoring."
                )

            prefix_tokens = tokenizer.encode(
                SYSTEM_PREFIX,
                add_special_tokens=False,
            )
            suffix_tokens = tokenizer.encode(
                ASSISTANT_SUFFIX,
                add_special_tokens=False,
            )
            if len(prefix_tokens) + len(suffix_tokens) >= self.max_length:
                raise ValueError(
                    "max_length is too small for the Qwen3 reranker prompt."
                )

            # Publish the fully initialized objects only after every setup
            # step has succeeded, so another request cannot see a partial load.
            self._torch = torch
            self._device = device
            self._tokenizer = tokenizer
            self._model = model
            self._token_true_id = int(true_ids[0])
            self._token_false_id = int(false_ids[0])
            self._prefix_tokens = prefix_tokens
            self._suffix_tokens = suffix_tokens

            logger.info(
                "Qwen3 reranker '%s' loaded successfully on %s.",
                self.model_name,
                device,
            )

    def _format_pair(self, query: str, document: str) -> str:
        truncated_document = document[: self.max_document_chars]
        return (
            f"<Instruct>: {self.instruction}\n\n"
            f"<Query>: {query.strip()}\n\n"
            f"<Document>: {truncated_document}"
        )

    def _score_pair(self, query: str, document: str) -> float:
        """Return P(yes) from the final-position yes/no logits."""
        self._ensure_model_loaded()

        assert self._torch is not None
        assert self._tokenizer is not None
        assert self._model is not None
        assert self._device is not None
        assert self._token_true_id is not None
        assert self._token_false_id is not None

        torch = self._torch
        tokenizer = self._tokenizer
        text = self._format_pair(query, document)
        reserved_tokens = len(self._prefix_tokens) + len(self._suffix_tokens)
        content_max_length = self.max_length - reserved_tokens

        # Follow the official model-card preprocessing: tokenize the pair,
        # truncate it to the room left after prefix/suffix tokens, then wrap it.
        encoded = tokenizer(
            text,
            truncation=True,
            max_length=content_max_length,
            return_attention_mask=False,
        )
        content_tokens = encoded["input_ids"]
        input_ids = self._prefix_tokens + content_tokens + self._suffix_tokens
        input_tensor = torch.tensor(
            [input_ids],
            dtype=torch.long,
            device=self._device,
        )
        attention_mask = torch.ones_like(input_tensor)

        with torch.inference_mode():
            outputs = self._model(
                input_ids=input_tensor,
                attention_mask=attention_mask,
            )
            next_token_logits = outputs.logits[0, -1, :]
            binary_logits = torch.stack(
                [
                    next_token_logits[self._token_false_id],
                    next_token_logits[self._token_true_id],
                ]
            )
            probability_yes = torch.softmax(binary_logits, dim=0)[1].item()

        return float(probability_yes)

    def warm_up(self) -> None:
        """Load the model and run one real scoring operation."""
        logger.info("Warming up Transformers reranker '%s'...", self.model_name)
        with self._inference_lock:
            score = self._score_pair(
                "What is the store return policy?",
                "Customers can return eligible products according to the store's return policy.",
            )
        logger.info(
            "Transformers reranker '%s' is ready (warm-up score=%.4f).",
            self.model_name,
            score,
        )

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
        # Sequential scoring keeps peak memory lower on CPU-only machines.
        # The same lock prevents overlapping warm-up and request inference.
        with self._inference_lock:
            for document in documents:
                payload = document.get("payload") or {}
                text = str(payload.get("text", "")).strip()
                score = self._score_pair(query.strip(), text) if text else 0.0
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
