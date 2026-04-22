"""
Knowledge Base API endpoints.

POST   /api/v1/knowledge/upload   — Upload a PDF to the knowledge base
GET    /api/v1/knowledge          — List all documents in the knowledge base
GET    /api/v1/knowledge/search   — Semantic search across stored documents
DELETE /api/v1/knowledge/{doc_id} — Remove a document from the knowledge base
POST   /api/v1/knowledge/ask      — RAG: ask a question with retrieved context
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from typing import Optional

from services.knowledge_base import (
    ingest_pdf,
    list_documents,
    delete_document,
    search as kb_search,
)
from services.rag import answer_with_context

knowledge_router = APIRouter(tags=["knowledge"])

MAX_FILE_SIZE = 25 * 1024 * 1024  # 25 MB


@knowledge_router.post("/knowledge/upload")
async def upload_to_knowledge_base(file: UploadFile = File(...)):
    """Upload a PDF and store its chunks in the vector knowledge base."""
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    pdf_bytes = await file.read()

    if len(pdf_bytes) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File exceeds 25 MB limit")

    try:
        result = ingest_pdf(pdf_bytes=pdf_bytes, filename=file.filename)
    except ValueError as e:
        if "SCANNED_PDF" in str(e):
            raise HTTPException(
                status_code=422,
                detail="PDF appears to be scanned/image-based. Only text PDFs are supported.",
            )
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process PDF: {str(e)}")

    return {
        "status": "success",
        "message": f"Stored {result['chunks_stored']} chunks from {result['pages_processed']} pages",
        **result,
    }


@knowledge_router.get("/knowledge")
async def list_knowledge_base():
    """List all documents currently in the knowledge base."""
    docs = list_documents()
    return {
        "status": "success",
        "documents": docs,
        "total": len(docs),
    }


@knowledge_router.get("/knowledge/search")
async def search_knowledge_base(
    q: str = Query(..., description="Search query"),
    n: int = Query(5, ge=1, le=20, description="Number of results"),
    doc_id: Optional[str] = Query(None, description="Filter to a specific document"),
):
    """Semantic search across stored documents."""
    if not q.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    results = kb_search(query=q, n_results=n, doc_id=doc_id)

    return {
        "status": "success",
        "query": q,
        "results": results,
        "total": len(results),
    }


@knowledge_router.delete("/knowledge/{doc_id}")
async def remove_from_knowledge_base(doc_id: str):
    """Delete a document and all its chunks from the knowledge base."""
    try:
        result = delete_document(doc_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return {
        "status": "success",
        "message": f"Deleted {result['chunks_deleted']} chunks",
        **result,
    }


@knowledge_router.post("/knowledge/ask")
async def ask_knowledge_base(
    question: str = Query(..., description="Your question"),
    doc_id: Optional[str] = Query(None, description="Scope to a specific document"),
    n_chunks: int = Query(5, ge=1, le=20, description="Context chunks to retrieve"),
):
    """
    RAG endpoint: retrieve relevant context from the knowledge base
    and generate an LLM-powered answer.

    Requires LLM_API_KEY to be set.
    """
    if not question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    try:
        result = await answer_with_context(
            question=question,
            doc_id=doc_id,
            n_chunks=n_chunks,
        )
    except RuntimeError as e:
        if "LLM_API_KEY" in str(e):
            raise HTTPException(
                status_code=503,
                detail="LLM not configured. Set LLM_API_KEY environment variable.",
            )
        raise HTTPException(status_code=500, detail=str(e))

    return {
        "status": "success",
        **result,
    }
