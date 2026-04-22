"""
Knowledge Base service — ChromaDB + sentence-transformers embeddings.

Stores uploaded document chunks as vectors for retrieval-augmented generation.
Uses the all-MiniLM-L6-v2 model for local embeddings (no API key needed).
"""

import uuid
from typing import Optional

import chromadb
from sentence_transformers import SentenceTransformer

from services.pdf_parser import extract_pages, chunk_pages
from config import CHROMA_PERSIST_DIR, EMBEDDING_MODEL

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
COLLECTION_NAME = "bidagent_knowledge"

# ---------------------------------------------------------------------------
# Singletons (lazy-loaded)
# ---------------------------------------------------------------------------
_chroma_client: Optional[chromadb.ClientAPI] = None
_embedding_model: Optional[SentenceTransformer] = None


def _get_chroma_client() -> chromadb.ClientAPI:
    global _chroma_client
    if _chroma_client is None:
        _chroma_client = chromadb.PersistentClient(
            path=CHROMA_PERSIST_DIR,
            settings=chromadb.Settings(anonymized_telemetry=False),
        )
    return _chroma_client


def _get_embedding_model() -> SentenceTransformer:
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = SentenceTransformer(EMBEDDING_MODEL)
    return _embedding_model


def _get_collection():
    client = _get_chroma_client()
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


# ---------------------------------------------------------------------------
# Embed helper
# ---------------------------------------------------------------------------
def _embed_texts(texts: list[str]) -> list[list[float]]:
    model = _get_embedding_model()
    embeddings = model.encode(texts, show_progress_bar=False)
    return embeddings.tolist()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def ingest_pdf(pdf_bytes: bytes, filename: str) -> dict:
    """
    Extract text from a PDF, chunk it, embed the chunks, and store in ChromaDB.
    Returns metadata about what was stored.
    """
    doc_id = uuid.uuid4().hex[:12]
    pages = extract_pages(pdf_bytes)
    chunks = chunk_pages(pages)

    if not chunks:
        raise ValueError("No text chunks extracted from PDF")

    texts = [c["text"] for c in chunks]
    embeddings = _embed_texts(texts)

    ids = [f"{doc_id}_{c['chunk_id']}" for c in chunks]
    metadatas = [
        {
            "doc_id": doc_id,
            "filename": filename,
            "page": c["page"],
            "chunk_id": c["chunk_id"],
        }
        for c in chunks
    ]

    collection = _get_collection()
    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=texts,
        metadatas=metadatas,
    )

    return {
        "doc_id": doc_id,
        "filename": filename,
        "chunks_stored": len(chunks),
        "pages_processed": len(pages),
    }


def search(query: str, n_results: int = 5, doc_id: Optional[str] = None) -> list[dict]:
    """
    Semantic search across the knowledge base.
    Optionally filter to a specific document by doc_id.
    """
    collection = _get_collection()

    query_embedding = _embed_texts([query])[0]

    where_filter = {"doc_id": doc_id} if doc_id else None

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        where=where_filter,
        include=["documents", "metadatas", "distances"],
    )

    matches = []
    if results and results["ids"] and results["ids"][0]:
        for i, chunk_id in enumerate(results["ids"][0]):
            matches.append({
                "chunk_id": chunk_id,
                "text": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i],
                "relevance": round(1 - results["distances"][0][i], 4),
            })

    return matches


def list_documents() -> list[dict]:
    """List all unique documents in the knowledge base."""
    collection = _get_collection()

    all_items = collection.get(include=["metadatas"])

    docs = {}
    for meta in all_items["metadatas"]:
        did = meta["doc_id"]
        if did not in docs:
            docs[did] = {
                "doc_id": did,
                "filename": meta["filename"],
                "chunk_count": 0,
            }
        docs[did]["chunk_count"] += 1

    return list(docs.values())


def delete_document(doc_id: str) -> dict:
    """Delete all chunks for a given document from the knowledge base."""
    collection = _get_collection()

    # Get all IDs for this doc
    all_items = collection.get(
        where={"doc_id": doc_id},
        include=["metadatas"],
    )

    if not all_items["ids"]:
        raise ValueError(f"Document {doc_id} not found")

    collection.delete(ids=all_items["ids"])

    return {
        "doc_id": doc_id,
        "chunks_deleted": len(all_items["ids"]),
    }
