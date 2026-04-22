"""
Bid Builder API endpoints.

POST /api/v1/bid/extract-sections    — Extract answerable sections from uploaded tender
POST /api/v1/bid/generate-response   — Generate a bid response (single pass)
POST /api/v1/bid/generate-pipeline   — Run full 4-phase pipeline with SSE progress
POST /api/v1/bid/compliance          — Run compliance matrix check against drafts
"""

import json
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from services.rag import answer_with_context
from services.knowledge_base import search as kb_search
from services.llm import generate_text
from services.agent_tools import (
    analyze_evidence_gaps,
    generate_draft,
    squeeze_word_count,
    restyle_tone,
    score_against_rubric,
    compliance_check,
)
from services.auth import get_current_user

bid_router = APIRouter(prefix="/bid", tags=["bid"])

WORD_LIMIT = 250

EXTRACT_SECTIONS_PROMPT = """You are analyzing a tender/RFP document. Extract ALL sections, questions, or requirements that need a written response from the bidder.

For each section found, provide:
- id: a short unique slug (e.g. "tech-approach", "team-experience", "social-value")
- title: the section heading or question as it appears in the document
- description: a brief summary of what the section asks for
- word_limit: the word limit if specified, otherwise null

Return a JSON array of objects. Example:
[
  {"id": "tech-approach", "title": "Technical Approach", "description": "Describe your proposed technical solution and methodology", "word_limit": 250},
  {"id": "team-exp", "title": "Team Experience", "description": "Demonstrate relevant experience of your proposed team", "word_limit": null}
]

Return ONLY valid JSON, no markdown fences, no explanation."""


class ExtractRequest(BaseModel):
    doc_id: str | None = None
    tender_name: str = ""


class GenerateRequest(BaseModel):
    section_title: str
    section_description: str = ""
    doc_id: str | None = None
    word_limit: int = WORD_LIMIT


class PipelineRequest(BaseModel):
    section_title: str
    section_description: str = ""
    doc_id: str | None = None
    session_id: str = ""
    section_id: str = ""


@bid_router.post("/extract-sections")
async def extract_sections(req: ExtractRequest, _user=Depends(get_current_user)):
    """Extract sections from the uploaded tender document using LLM."""

    # Get all chunks from the tender to give the LLM full context
    chunks = kb_search(query="requirements questions sections criteria response", n_results=20, doc_id=req.doc_id)

    if not chunks:
        raise HTTPException(status_code=422, detail="No content found in the uploaded document")

    # Build document text from chunks
    doc_text = "\n\n".join(
        f"[Page {c.get('metadata', {}).get('page', '?')}]\n{c['text']}"
        for c in chunks
    )

    prompt = f"Tender document content:\n\n{doc_text}\n\n{EXTRACT_SECTIONS_PROMPT}"

    try:
        raw = await generate_text(prompt)
    except RuntimeError as e:
        if "LLM_API_KEY" in str(e):
            raise HTTPException(status_code=503, detail="LLM not configured")
        raise HTTPException(status_code=500, detail=str(e))

    # Parse LLM response
    try:
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[1]
            cleaned = cleaned.rsplit("```", 1)[0]
        sections = json.loads(cleaned)
    except (json.JSONDecodeError, IndexError):
        raise HTTPException(status_code=500, detail=f"Failed to parse sections from tender. LLM response: {raw[:500]}")

    # Ensure each section has required fields
    for i, s in enumerate(sections):
        if "id" not in s:
            s["id"] = f"section-{i}"
        if "title" not in s:
            s["title"] = f"Section {i + 1}"
        if "description" not in s:
            s["description"] = ""

    return {
        "status": "success",
        "tender_name": req.tender_name or "Untitled Tender",
        "sections": sections,
    }


@bid_router.post("/generate-response")
async def generate_response(req: GenerateRequest, _user=Depends(get_current_user)):
    """Generate a bid response for a specific section using RAG (single pass)."""
    question = f"{req.section_title}: {req.section_description}" if req.section_description else req.section_title

    try:
        result = await answer_with_context(question=question, doc_id=req.doc_id, n_chunks=5)
    except RuntimeError as e:
        if "LLM_API_KEY" in str(e):
            raise HTTPException(status_code=503, detail="LLM not configured")
        raise HTTPException(status_code=500, detail=str(e))

    answer = result["answer"]
    return {
        "status": "success",
        "text": answer,
        "word_count": len(answer.split()),
        "word_limit": req.word_limit,
        "sources": result.get("sources", []),
    }


@bid_router.post("/generate-pipeline")
async def generate_pipeline(req: PipelineRequest, _user=Depends(get_current_user)):
    """Run the full 4-phase bid generation pipeline with SSE progress updates."""

    async def event_stream():
        def sse(data: dict) -> str:
            return f"data: {json.dumps(data, default=str)}\n\n"

        try:
            # Phase A: Evidence Gap Analysis
            yield sse({"phase": "A", "status": "running", "label": "Analyzing evidence gaps..."})
            gaps_result = await analyze_evidence_gaps(
                section_title=req.section_title,
                section_description=req.section_description,
            )
            yield sse({"phase": "A", "status": "done", "result": gaps_result})

            # Phase B: Draft & Squeeze
            yield sse({"phase": "B", "status": "running", "label": "Generating draft..."})
            draft_result = await generate_draft(
                section_title=req.section_title,
                section_description=req.section_description,
            )
            draft_text = draft_result.get("draft", "")
            yield sse({"phase": "B_draft", "status": "done", "word_count": draft_result.get("word_count", 0)})

            yield sse({"phase": "B", "status": "running", "label": "Squeezing to word limit..."})
            squeeze_result = await squeeze_word_count(text=draft_text, target_max=249)
            draft_text = squeeze_result.get("text", draft_text)
            yield sse({"phase": "B", "status": "done", "result": {"word_count": squeeze_result.get("word_count", 0)}})

            # Phase C: Tone Styling
            yield sse({"phase": "C", "status": "running", "label": "Applying public sector tone..."})
            tone_result = await restyle_tone(text=draft_text)
            draft_text = tone_result.get("text", draft_text)
            yield sse({"phase": "C", "status": "done", "result": {"word_count": tone_result.get("word_count", 0)}})

            # Phase D: Red Team Scoring
            yield sse({"phase": "D", "status": "running", "label": "Scoring against rubric..."})
            score_result = await score_against_rubric(text=draft_text, section_title=req.section_title)
            yield sse({"phase": "D", "status": "done", "result": score_result})

            # Final result
            yield sse({
                "phase": "complete",
                "final_draft": draft_text,
                "word_count": len(draft_text.split()),
                "score": score_result.get("score"),
                "gaps": gaps_result,
                "sources": draft_result.get("sources", []),
            })

        except Exception as e:
            yield sse({"phase": "error", "error": str(e)})

    return StreamingResponse(event_stream(), media_type="text/event-stream")


class ComplianceRequest(BaseModel):
    drafts: str = ""


@bid_router.post("/compliance")
async def run_compliance_check(req: ComplianceRequest, _user=Depends(get_current_user)):
    """Run compliance matrix check: extract tender requirements and check coverage."""
    try:
        result = await compliance_check(drafts=req.drafts)
    except RuntimeError as e:
        if "LLM_API_KEY" in str(e):
            raise HTTPException(status_code=503, detail="LLM not configured")
        raise HTTPException(status_code=500, detail=str(e))

    return {"status": "success", **result}
