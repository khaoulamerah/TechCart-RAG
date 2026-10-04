from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from datetime import datetime, timezone
from time import perf_counter
from typing import Any
from uuid import uuid4

from fastapi import HTTPException, status

from backend.rag.generator.base import LLMProvider, LLMProviderError
from backend.rag.prompt import build_rag_prompt
from backend.rag.retriever.retriever import Retriever
from backend.repositories.rag_trace import RAGTraceRepository
from backend.services.conversation import ConversationService


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ChatService:
    def __init__(
        self,
        conversation_service: ConversationService,
        llm_provider: LLMProvider,
        retriever: Retriever,
        rag_trace_repository: RAGTraceRepository,
    ) -> None:
        self.conversation_service = conversation_service
        self.llm_provider = llm_provider
        self.retriever = retriever
        self.rag_trace_repository = rag_trace_repository

    async def prepare_conversation(
        self,
        message: str,
        session_id: str | None,
        conversation_id: str | None,
    ) -> dict[str, Any]:
        cleaned_message = (message or "").strip()

        if not cleaned_message:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Message cannot be empty.",
            )

        if conversation_id:
            try:
                conversation = await self.conversation_service.get_conversation(
                    conversation_id
                )
                return {
                    "cleaned_message": cleaned_message,
                    "conversation_id": conversation["id"],
                    "session_id": conversation["session_id"],
                }
            except HTTPException as exc:
                if exc.status_code != status.HTTP_404_NOT_FOUND:
                    raise

        resolved_session_id = session_id or str(uuid4())
        conversation = await self.conversation_service.get_or_create_by_session(
            resolved_session_id
        )

        return {
            "cleaned_message": cleaned_message,
            "conversation_id": conversation["id"],
            "session_id": conversation["session_id"],
        }

    @staticmethod
    def _context_from_results(
        results: list[dict[str, Any]],
    ) -> list[str]:
        context: list[str] = []

        for result in results:
            payload = result.get("payload") or {}
            text = str(payload.get("text", "")).strip()
            if not text:
                continue

            document_id = payload.get("document_id", "unknown")
            chunk_id = payload.get("chunk_id", "unknown")
            score = result.get("rerank_score", result.get("score", 0.0))

            context.append(
                f"Document: {document_id}\n"
                f"Chunk: {chunk_id}\n"
                f"Score: {float(score):.4f}\n"
                f"Content:\n{text}"
            )

        return context

    async def _save_trace(self, trace: dict[str, Any]) -> None:
        """Tracing must never break the user-facing chat request."""
        try:
            await self.rag_trace_repository.create(trace)
        except Exception:
            # Logging can be added here later; observability failures should
            # never make an otherwise valid RAG response fail.
            return

    async def stream_message(
        self,
        message: str,
        session_id: str | None = None,
        conversation_id: str | None = None,
    ) -> AsyncIterator[dict[str, Any]]:
        """Run the RAG pipeline and persist an observability trace."""
        conversation_data = await self.prepare_conversation(
            message=message,
            session_id=session_id,
            conversation_id=conversation_id,
        )

        cleaned_message = conversation_data["cleaned_message"]
        conversation_id = conversation_data["conversation_id"]
        session_id = conversation_data["session_id"]

        user_conversation = await self.conversation_service.add_message(
            conversation_id,
            {
                "role": "user",
                "content": cleaned_message,
            },
        )

        messages = user_conversation.get("messages", [])
        message_id = messages[-1].get("message_id") if messages else None

        yield {
            "type": "metadata",
            "conversation_id": conversation_id,
            "session_id": session_id,
        }

        trace_started = perf_counter()
        trace: dict[str, Any] = {
            "conversation_id": conversation_id,
            "message_id": message_id,
            "question": cleaned_message,
            "created_at": utcnow(),
            "retrieval": None,
            "reranking": None,
            "llm": None,
            "context": [],
            "prompt": None,
            "total_latency_ms": 0.0,
            "status": "success",
            "error": None,
        }

        try:
            # -------------------------------------------------
            # Retrieval + reranking
            # -------------------------------------------------
            retrieved_results, retrieval_trace = await asyncio.to_thread(
                self.retriever.retrieve_with_trace,
                cleaned_message,
            )

            trace["retrieval"] = retrieval_trace.get("retrieval")
            trace["reranking"] = retrieval_trace.get("reranking")

            # -------------------------------------------------
            # Context + prompt
            # -------------------------------------------------
            trace["context"] = self._context_from_results(
                retrieved_results
            )

            prompt = build_rag_prompt(
                question=cleaned_message,
                results=retrieved_results,
            )
            trace["prompt"] = prompt

            # -------------------------------------------------
            # LLM streaming
            # -------------------------------------------------
            full_response: list[str] = []
            llm_started = perf_counter()
            first_token_at: float | None = None

            async for chunk in self.llm_provider.generate_stream(prompt):
                if not chunk:
                    continue

                if first_token_at is None:
                    first_token_at = perf_counter()

                full_response.append(chunk)

                yield {
                    "type": "token",
                    "content": chunk,
                }

            llm_finished = perf_counter()

            trace["llm"] = {
                "provider": type(self.llm_provider).__name__,
                "model": getattr(
                    self.llm_provider,
                    "model",
                    None,
                ),
                "time_to_first_token_ms": (
                    (first_token_at - llm_started) * 1000
                    if first_token_at is not None
                    else None
                ),
                "latency_ms": (llm_finished - llm_started) * 1000,
                "response": "".join(full_response),
                "context": trace["context"],
            }

            reply_text = "".join(full_response).strip()

            if not reply_text:
                raise LLMProviderError(
                    "The AI model returned an empty response."
                )

            await self.conversation_service.add_message(
                conversation_id,
                {
                    "role": "assistant",
                    "content": reply_text,
                },
            )

            trace["total_latency_ms"] = (
                perf_counter() - trace_started
            ) * 1000
            await self._save_trace(trace)

            yield {
                "type": "done",
                "conversation_id": conversation_id,
                "session_id": session_id,
                "created_at": utcnow().isoformat(),
            }

        except Exception as exc:
            trace["status"] = "error"
            trace["error"] = str(exc)
            trace["total_latency_ms"] = (
                perf_counter() - trace_started
            ) * 1000
            await self._save_trace(trace)

            if isinstance(exc, LLMProviderError):
                message_text = "The AI model is currently unavailable."
            elif trace.get("retrieval") is None:
                message_text = "The knowledge base is currently unavailable."
            else:
                message_text = "An error occurred while generating the response."

            yield {
                "type": "error",
                "message": message_text,
            }
