"""
RAG service — retrieves context from the knowledge base and builds
augmented prompts for the LLM.

Usage:
    from services.rag import answer_with_context

    result = await answer_with_context(
        question="What is the submission deadline?",
        doc_id="abc123",       # optional — scope to one document
        n_chunks=5,            # how many chunks to retrieve
    )
"""

from typing import Optional

from services.knowledge_base import search as kb_search
from services.llm import generate_text


SYSTEM_PROMPT = """You are BidAgent, an AI assistant that helps teams respond to government and enterprise tenders.

Answer the user's question using ONLY the context provided below. If the context does not contain enough information to answer, say so clearly — do not make up facts.

When citing information, reference the source page number in parentheses, e.g. (Page 3).

Keep answers concise, factual, and actionable."""


def retrieve_context(
    query: str,
    n_results: int = 5,
    doc_id: Optional[str] = None,
) -> list[dict]:
    """
    Retrieve the most relevant chunks from the knowledge base.
    Returns a list of match dicts with text, metadata, and relevance score.
    """
    return kb_search(query=query, n_results=n_results, doc_id=doc_id)


def build_prompt(question: str, context_chunks: list[dict]) -> str:
    """
    Assemble the user prompt from the question and retrieved context.
    """
    if not context_chunks:
        return (
            f"Question: {question}\n\n"
            "No relevant context was found in the knowledge base. "
            "Please let the user know."
        )

    context_parts = []
    for i, chunk in enumerate(context_chunks, 1):
        page = chunk.get("metadata", {}).get("page", "?")
        filename = chunk.get("metadata", {}).get("filename", "unknown")
        relevance = chunk.get("relevance", 0)
        context_parts.append(
            f"--- Source {i} (Page {page}, {filename}, relevance {relevance}) ---\n"
            f"{chunk['text']}\n"
        )

    context_block = "\n".join(context_parts)

    return (
        f"Context:\n{context_block}\n"
        f"---\n\n"
        f"Question: {question}\n\n"
        f"Answer based on the context above:"
    )


async def answer_with_context(
    question: str,
    doc_id: Optional[str] = None,
    n_chunks: int = 5,
) -> dict:
    """
    End-to-end RAG: retrieve context → build prompt → call LLM → return answer.

    Returns:
        {
            "answer": str,
            "sources": [...],   # the chunks used as context
            "question": str,
        }
    """
    # 1. Retrieve
    chunks = retrieve_context(query=question, n_results=n_chunks, doc_id=doc_id)

    # 2. Build prompt
    prompt = build_prompt(question, chunks)

    # 3. Call LLM
    answer = await generate_text(prompt=prompt, system_prompt=SYSTEM_PROMPT)

    # 4. Return structured response
    sources = [
        {
            "page": c.get("metadata", {}).get("page"),
            "filename": c.get("metadata", {}).get("filename"),
            "relevance": c.get("relevance"),
            "excerpt": c["text"][:300],
        }
        for c in chunks
    ]

    return {
        "answer": answer,
        "sources": sources,
        "question": question,
    }
