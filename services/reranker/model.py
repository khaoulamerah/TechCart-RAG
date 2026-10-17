"""Qwen3-Reranker model wrapper using the official Transformers scoring recipe."""

from __future__ import annotations

import logging
import math
import threading
from typing import Any

logger = logging.getLogger("techcart.reranker_service.model")

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


class Qwen3Reranker:
    """Score query-document pairs with Qwen3-Reranker-0.6B.

    The model is loaded only once. Scores are probabilities derived by applying
    softmax to the final-position logits for the `no` and `yes` tokens, which is
    the scoring approach documented in the official Qwen3-Reranker model card.
    """

    def __init__(
        self,
        model_name: str = "Qwen/Qwen3-Reranker-0.6B",
        device: str = "cpu",
        max_length: int = 2048,
        instruction: str = DEFAULT_INSTRUCTION,
        max_document_chars: int = 12000,
        batch_size: int = 2,
    ) -> None:
        if not model_name.strip():
            raise ValueError("model_name cannot be empty.")
        if device not in {"auto", "cpu", "cuda"}:
            raise ValueError("device must be 'auto', 'cpu', or 'cuda'.")
        if max_length < 128:
            raise ValueError("max_length must be at least 128 tokens.")
        if not instruction.strip():
            raise ValueError("instruction cannot be empty.")
        if max_document_chars <= 0:
            raise ValueError("max_document_chars must be positive.")
        if batch_size <= 0:
            raise ValueError("batch_size must be positive.")

        self.model_name = model_name.strip()
        self.device_preference = device
        self.max_length = int(max_length)
        self.instruction = instruction.strip()
        self.max_document_chars = int(max_document_chars)
        self.batch_size = int(batch_size)

        self._torch: Any | None = None
        self._tokenizer: Any | None = None
        self._model: Any | None = None
        self._device: str | None = None
        self._prefix_tokens: list[int] = []
        self._suffix_tokens: list[int] = []
        self._token_true_id: int | None = None
        self._token_false_id: int | None = None
        self._load_lock = threading.Lock()
        self._inference_lock = threading.Lock()

    def _ensure_model_loaded(self) -> None:
        """Load model/tokenizer safely on first use."""
        if self._model is not None and self._tokenizer is not None:
            return

        with self._load_lock:
            if self._model is not None and self._tokenizer is not None:
                return

            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer

            if self.device_preference == "auto":
                device = "cuda" if torch.cuda.is_available() else "cpu"
            else:
                device = self.device_preference

            if device == "cuda" and not torch.cuda.is_available():
                raise RuntimeError(
                    "RERANKER_DEVICE=cuda but CUDA is unavailable inside the "
                    "reranker container. Use cpu or configure a CUDA image/runtime."
                )

            dtype = torch.float16 if device == "cuda" else torch.float32
            logger.info(
                "Loading model %s on %s (dtype=%s)",
                self.model_name,
                device,
                dtype,
            )

            tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                padding_side="left",
            )
            if tokenizer.pad_token_id is None:
                tokenizer.pad_token = tokenizer.eos_token

            model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                torch_dtype=dtype,
            )
            model.to(device)
            model.eval()

            # Use the same token lookup as the official model-card example.
            token_true_id = tokenizer.convert_tokens_to_ids("yes")
            token_false_id = tokenizer.convert_tokens_to_ids("no")
            unknown_id = tokenizer.unk_token_id
            if (
                token_true_id is None
                or token_false_id is None
                or token_true_id == unknown_id
                or token_false_id == unknown_id
            ):
                raise RuntimeError(
                    "The tokenizer could not resolve the expected 'yes'/'no' tokens."
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
                raise ValueError("max_length is too small for the reranker prompt.")

            # Publish only completely initialized components.
            self._torch = torch
            self._tokenizer = tokenizer
            self._model = model
            self._device = device
            self._token_true_id = int(token_true_id)
            self._token_false_id = int(token_false_id)
            self._prefix_tokens = prefix_tokens
            self._suffix_tokens = suffix_tokens

            logger.info("Model %s loaded on %s", self.model_name, device)

    def _format_pair(self, query: str, document: str) -> str:
        """Format the query/document pair as specified by the model card."""
        return (
            f"<Instruct>: {self.instruction}\n"
            f"<Query>: {query.strip()}\n"
            f"<Document>: {document[:self.max_document_chars]}"
        )

    def score_documents(self, query: str, documents: list[str]) -> list[float]:
        """Return one P(yes) score per document, preserving input order."""
        if not query or not query.strip():
            raise ValueError("Query cannot be empty.")
        if not documents:
            return []
        if any(not isinstance(document, str) for document in documents):
            raise ValueError("Every document must be a string.")

        self._ensure_model_loaded()
        assert self._torch is not None
        assert self._tokenizer is not None
        assert self._model is not None
        assert self._device is not None
        assert self._token_true_id is not None
        assert self._token_false_id is not None

        torch = self._torch
        tokenizer = self._tokenizer
        content_max_length = (
            self.max_length - len(self._prefix_tokens) - len(self._suffix_tokens)
        )
        formatted = [
            self._format_pair(query, document)
            for document in documents
        ]
        all_scores: list[float] = []

        # Sequential batches bound peak CPU RAM and prevent concurrent model use.
        with self._inference_lock:
            for start in range(0, len(formatted), self.batch_size):
                batch_texts = formatted[start : start + self.batch_size]
                tokenized = tokenizer(
                    batch_texts,
                    padding=False,
                    truncation="longest_first",
                    return_attention_mask=False,
                    max_length=content_max_length,
                )
                wrapped_ids = [
                    self._prefix_tokens + token_ids + self._suffix_tokens
                    for token_ids in tokenized["input_ids"]
                ]
                model_inputs = tokenizer.pad(
                    {"input_ids": wrapped_ids},
                    padding=True,
                    return_tensors="pt",
                    max_length=self.max_length,
                )
                model_inputs = {
                    key: value.to(self._device)
                    for key, value in model_inputs.items()
                }

                with torch.inference_mode():
                    outputs = self._model(**model_inputs)
                    next_token_logits = outputs.logits[:, -1, :]
                    binary_logits = torch.stack(
                        [
                            next_token_logits[:, self._token_false_id],
                            next_token_logits[:, self._token_true_id],
                        ],
                        dim=1,
                    )
                    batch_scores = torch.softmax(binary_logits, dim=1)[:, 1]
                    scores = batch_scores.detach().cpu().tolist()

                for score in scores:
                    value = float(score)
                    if not math.isfinite(value):
                        raise RuntimeError("The reranker produced a non-finite score.")
                    all_scores.append(value)

        if len(all_scores) != len(documents):
            raise RuntimeError("The reranker returned an unexpected score count.")
        return all_scores

    def warm_up(self) -> None:
        """Load weights and run one real inference before declaring readiness."""
        score = self.score_documents(
            "What is the store return policy?",
            [
                "Customers can return eligible products according to the store's policy."
            ],
        )[0]
        logger.info("Reranker warm-up completed (score=%.4f)", score)
