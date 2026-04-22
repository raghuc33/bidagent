"""Agent tools — definitions and implementations for the bid-writing agent."""

import json
from services.knowledge_base import search as kb_search
from services.rag import answer_with_context
from services.llm import generate_text


# ---------------------------------------------------------------------------
# Tool definitions (OpenAI function-calling format)
# ---------------------------------------------------------------------------

TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "search_knowledge_base",
            "description": "Semantic search across uploaded tender documents and evidence. Use this to find relevant content.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "n": {"type": "integer", "description": "Number of results (default 5)", "default": 5},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "generate_draft",
            "description": "Generate a full bid section draft using RAG context from the knowledge base. Produces a ~400 word initial draft.",
            "parameters": {
                "type": "object",
                "properties": {
                    "section_title": {"type": "string", "description": "Section title to generate for"},
                    "section_description": {"type": "string", "description": "What this section should cover"},
                },
                "required": ["section_title"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "squeeze_word_count",
            "description": "Rewrite text to fit within a target word count (240-249 words). Removes filler while preserving evidence markers.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Text to squeeze"},
                    "target_max": {"type": "integer", "description": "Maximum word count", "default": 249},
                },
                "required": ["text"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "score_against_rubric",
            "description": "Score a draft 0-100 against evaluation criteria. Acts as an independent Red Team evaluator. Returns score and improvement suggestions.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Draft text to score"},
                    "section_title": {"type": "string", "description": "Which section this is for"},
                },
                "required": ["text", "section_title"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "analyze_evidence_gaps",
            "description": "Identify what evidence is missing for a section. Compares available KB content against section requirements.",
            "parameters": {
                "type": "object",
                "properties": {
                    "section_title": {"type": "string", "description": "Section title"},
                    "section_description": {"type": "string", "description": "What the section requires"},
                },
                "required": ["section_title"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "restyle_tone",
            "description": "Rewrite text for UK public sector tone: authoritative, collaborative, outcome-focused, active voice.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Text to restyle"},
                },
                "required": ["text"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "compliance_check",
            "description": "Extract all mandatory requirements from the tender (shall/must/required statements) and check which ones are addressed in the current bid drafts. Returns a compliance matrix with status per requirement.",
            "parameters": {
                "type": "object",
                "properties": {
                    "drafts": {
                        "type": "string",
                        "description": "All current bid section drafts concatenated, so the tool can check coverage",
                    },
                },
                "required": ["drafts"],
            },
        },
    },
]


# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------

async def search_knowledge_base(query: str, n: int = 5, **_) -> dict:
    results = kb_search(query=query, n_results=n)
    return {
        "matches": len(results),
        "results": [
            {
                "text": r["text"][:300],
                "page": r.get("metadata", {}).get("page"),
                "filename": r.get("metadata", {}).get("filename"),
                "relevance": r.get("relevance", 0),
            }
            for r in results
        ],
    }


async def generate_draft(section_title: str, section_description: str = "", **_) -> dict:
    question = f"{section_title}: {section_description}" if section_description else section_title
    result = await answer_with_context(question=question, n_chunks=5)
    return {
        "draft": result["answer"],
        "word_count": len(result["answer"].split()),
        "sources": result.get("sources", []),
    }


async def squeeze_word_count(text: str, target_max: int = 249, **_) -> dict:
    prompt = (
        f"Rewrite the following text to be between 240 and {target_max} words. "
        "Remove filler and redundancy but preserve all evidence markers, citations, "
        "and technical specifics. Keep the same tone and structure.\n\n"
        f"Text ({len(text.split())} words):\n{text}"
    )
    result = await generate_text(prompt)
    return {"text": result, "word_count": len(result.split())}


async def score_against_rubric(text: str, section_title: str, **_) -> dict:
    prompt = (
        "You are an independent evaluator for UK Public Sector tenders. "
        "Score the following bid response on a scale of 0-100 based on these criteria:\n"
        "- Relevance to the question (25 points)\n"
        "- Specific evidence and examples (25 points)\n"
        "- Clarity and structure (20 points)\n"
        "- Professional tone (15 points)\n"
        "- Word economy (15 points)\n\n"
        f"Section: {section_title}\n\n"
        f"Response:\n{text}\n\n"
        "Return a JSON object with: score (number), breakdown (object with criterion scores), "
        "strengths (array of strings), improvements (array of strings). "
        "Return ONLY valid JSON, no markdown."
    )
    raw = await generate_text(prompt)
    try:
        # Strip markdown code fences if present
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[1]
            cleaned = cleaned.rsplit("```", 1)[0]
        return json.loads(cleaned)
    except (json.JSONDecodeError, IndexError):
        return {"score": 0, "raw_response": raw, "error": "Could not parse score"}


async def analyze_evidence_gaps(section_title: str, section_description: str = "", **_) -> dict:
    results = kb_search(query=section_title, n_results=10)
    evidence_summary = "\n".join(
        f"- {r['text'][:200]} (Page {r.get('metadata', {}).get('page', '?')})"
        for r in results[:5]
    )

    prompt = (
        f"Section: {section_title}\n"
        f"Description: {section_description}\n\n"
        f"Available evidence:\n{evidence_summary}\n\n"
        "Identify gaps: what evidence is missing or weak for this section? "
        "List 3-5 specific gaps. Be concise."
    )
    result = await generate_text(prompt)
    return {"gaps": result, "evidence_found": len(results)}


async def restyle_tone(text: str, **_) -> dict:
    prompt = (
        "Rewrite the following bid response for UK public sector tone:\n"
        "- Replace 'we did X' with 'we delivered X outcome for the taxpayer'\n"
        "- Use active voice to demonstrate accountability\n"
        "- Ensure focus on knowledge transfer where applicable\n"
        "- Sound authoritative yet collaborative\n"
        "- Preserve all facts, evidence, and page references\n"
        "- Keep the same word count (within ±5 words)\n\n"
        f"Text:\n{text}"
    )
    result = await generate_text(prompt)
    return {"text": result, "word_count": len(result.split())}


async def compliance_check(drafts: str = "", **_) -> dict:
    """Extract requirements from the tender and check coverage against drafts."""
    # Get all tender content from KB
    tender_chunks = kb_search(query="shall must required mandatory requirements criteria", n_results=20)

    if not tender_chunks:
        return {"error": "No tender content found in knowledge base", "requirements": []}

    tender_text = "\n\n".join(c["text"] for c in tender_chunks[:15])

    # Step 1: Extract requirements
    extract_prompt = (
        "Extract ALL mandatory requirements from this tender document. "
        "Look for statements containing 'shall', 'must', 'required', 'mandatory', 'essential'. "
        "For each requirement, provide:\n"
        "- id: short slug (e.g. 'security-clearance', 'iso-27001')\n"
        "- requirement: the exact requirement text (1-2 sentences)\n"
        "- category: one of 'technical', 'experience', 'compliance', 'staffing', 'commercial', 'security'\n"
        "- criticality: 'mandatory' or 'desirable'\n"
        "- page: page number if visible in the text\n\n"
        f"Tender content:\n{tender_text}\n\n"
        "Return a JSON array. Return ONLY valid JSON, no markdown."
    )
    raw_requirements = await generate_text(extract_prompt)

    try:
        cleaned = raw_requirements.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[1]
            cleaned = cleaned.rsplit("```", 1)[0]
        requirements = json.loads(cleaned)
    except (json.JSONDecodeError, IndexError):
        return {"error": "Failed to parse requirements", "raw": raw_requirements[:500]}

    if not drafts.strip():
        # No drafts yet — return requirements with unknown status
        for r in requirements:
            r["status"] = "not_checked"
            r["addressed_in"] = None
            r["notes"] = "No drafts available to check against"
        return {
            "requirements": requirements,
            "total": len(requirements),
            "addressed": 0,
            "gaps": len(requirements),
            "coverage_pct": 0,
        }

    # Step 2: Check each requirement against drafts
    check_prompt = (
        "You are checking a bid response against tender requirements.\n\n"
        f"BID RESPONSE DRAFTS:\n{drafts}\n\n"
        f"REQUIREMENTS:\n{json.dumps(requirements, indent=2)}\n\n"
        "For each requirement, determine:\n"
        "- status: 'addressed' (clearly covered in drafts), 'partial' (mentioned but not fully), or 'missing' (not addressed)\n"
        "- addressed_in: which section mentions it (or null)\n"
        "- notes: brief explanation of coverage or what's missing\n\n"
        "Return a JSON array with the same requirements plus these 3 fields added. "
        "Return ONLY valid JSON, no markdown."
    )
    raw_check = await generate_text(check_prompt)

    try:
        cleaned = raw_check.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[1]
            cleaned = cleaned.rsplit("```", 1)[0]
        checked = json.loads(cleaned)
    except (json.JSONDecodeError, IndexError):
        # Fallback: return requirements without check
        for r in requirements:
            r["status"] = "not_checked"
            r["addressed_in"] = None
            r["notes"] = "Check failed"
        checked = requirements

    addressed = sum(1 for r in checked if r.get("status") == "addressed")
    partial = sum(1 for r in checked if r.get("status") == "partial")
    missing = sum(1 for r in checked if r.get("status") == "missing")
    total = len(checked)

    return {
        "requirements": checked,
        "total": total,
        "addressed": addressed,
        "partial": partial,
        "gaps": missing,
        "coverage_pct": round((addressed + partial * 0.5) / total * 100) if total > 0 else 0,
    }


# ---------------------------------------------------------------------------
# Tool dispatcher
# ---------------------------------------------------------------------------

TOOL_FUNCTIONS = {
    "search_knowledge_base": search_knowledge_base,
    "generate_draft": generate_draft,
    "squeeze_word_count": squeeze_word_count,
    "score_against_rubric": score_against_rubric,
    "analyze_evidence_gaps": analyze_evidence_gaps,
    "restyle_tone": restyle_tone,
    "compliance_check": compliance_check,
}


async def execute_tool(name: str, arguments: dict) -> str:
    """Execute a tool by name and return the result as a JSON string."""
    fn = TOOL_FUNCTIONS.get(name)
    if not fn:
        return json.dumps({"error": f"Unknown tool: {name}"})

    try:
        result = await fn(**arguments)
        return json.dumps(result, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})
