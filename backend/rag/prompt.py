from typing import Any


SYSTEM_INSTRUCTION = """
You are TechCart, an AI assistant for an e-commerce store.

Answer the user's question using ONLY the provided context.

Rules:
- Do not invent products, prices, policies, specifications,
  or other information.
- If the context does not contain enough information,
  clearly say that the information is not available.
- Be concise and helpful.
- When the user asks about store policies, use the
  retrieved policy information.
- When comparing products, only use specifications
  present in the context.
- Answer in the same language as the user when possible.
""".strip()


def build_rag_prompt(
    question: str,
    results: list[dict[str, Any]],
) -> str:

    context_parts: list[str] = []

    for index, result in enumerate(
        results,
        start=1,
    ):
        payload = result.get(
            "payload",
            {},
        )

        document_id = payload.get(
            "document_id",
            "unknown",
        )

        chunk_id = payload.get(
            "chunk_id",
            "unknown",
        )

        text = payload.get(
            "text",
            "",
        )

        score = result.get(
            "score",
            0.0,
        )

        if not text:
            continue

        context_parts.append(
            (
                f"[Context {index}]\n"
                f"Document: {document_id}\n"
                f"Chunk: {chunk_id}\n"
                f"Similarity: {score:.4f}\n"
                f"Content:\n{text}"
            )
        )

    if context_parts:
        context = "\n\n".join(
            context_parts
        )
    else:
        context = (
            "No relevant context was found."
        )

    return f"""
{SYSTEM_INSTRUCTION}

Retrieved context:

{context}

User question:

{question}

Answer:
""".strip()