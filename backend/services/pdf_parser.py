import re
import uuid
import fitz  # PyMuPDF

MAX_CHARS = 4000

KEYWORD_QUERIES = {
    "due_date": ["due", "deadline", "received", "submit", "closing", "closing date", "application"],
    "bond": ["bid bond", "bond", "security"],
    "mandatory": ["shall", "must", "required"],
}

DATE_PATTERNS = [
    re.compile(r"\d{1,2}[-/]\d{1,2}[-/]\d{4}", re.IGNORECASE),
    re.compile(r"\d{4}[-/]\d{1,2}[-/]\d{1,2}", re.IGNORECASE),
    re.compile(
        r"(January|February|March|April|May|June|July|August|September|October|November|December)"
        r"\s+\d{1,2},\s+\d{4}",
        re.IGNORECASE,
    ),
    re.compile(
        r"\d{1,2}\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}",
        re.IGNORECASE,
    ),
]


def extract_pages(pdf_bytes: bytes):
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    pages = []

    for i, page in enumerate(doc):
        text = page.get_text().strip()
        pages.append({"page": i + 1, "text": text})

    total_text = sum(len(p["text"]) for p in pages)
    if total_text < 500:
        raise ValueError("SCANNED_PDF")

    return pages


def chunk_pages(pages):
    chunks = []
    for page in pages:
        text = page["text"]
        page_num = page["page"]
        for i in range(0, len(text), MAX_CHARS):
            chunk_text = text[i : i + MAX_CHARS].strip()
            if not chunk_text:
                continue
            chunks.append(
                {
                    "chunk_id": f"c_{uuid.uuid4().hex[:8]}",
                    "page": page_num,
                    "text": chunk_text,
                }
            )
    return chunks


def retrieve_chunks(chunks, keywords):
    matches = []
    for c in chunks:
        text_lower = c["text"].lower()
        if any(k in text_lower for k in keywords):
            matches.append(c)
    return matches[:8]


def extract_core_facts(chunks):
    facts = {"bid_due": None, "bond_required": False, "mandatory_items": []}

    for c in retrieve_chunks(chunks, KEYWORD_QUERIES["due_date"]):
        date_found = False
        for pattern in DATE_PATTERNS:
            m = pattern.search(c["text"])
            if m:
                match_text = m.group(0)
                start_pos = max(0, m.start() - 50)
                end_pos = min(len(c["text"]), m.end() + 50)
                context_quote = c["text"][start_pos:end_pos].strip()

                facts["bid_due"] = {
                    "value": match_text,
                    "evidence": [
                        {
                            "page": c["page"],
                            "chunk_id": c["chunk_id"],
                            "quote": context_quote,
                        }
                    ],
                }
                date_found = True
                break
        if date_found:
            break

    for c in retrieve_chunks(chunks, KEYWORD_QUERIES["bond"]):
        facts["bond_required"] = True
        facts.setdefault("bond_evidence", []).append(
            {"page": c["page"], "chunk_id": c["chunk_id"], "quote": c["text"][:200]}
        )
        break

    for c in retrieve_chunks(chunks, KEYWORD_QUERIES["mandatory"]):
        facts["mandatory_items"].append(
            {
                "text": "Mandatory requirement detected",
                "page": c["page"],
                "chunk_id": c["chunk_id"],
                "quote": c["text"][:200],
            }
        )

    return facts


def decide_go_no_go(facts):
    if not facts.get("bid_due"):
        return {
            "decision": "NEEDS_INFO",
            "confidence": 0.45,
            "reason": "Bid due date not clearly found in document",
        }

    if facts.get("bond_required"):
        return {
            "decision": "NEEDS_INFO",
            "confidence": 0.55,
            "reason": "Bid bond requirement detected; company capability unknown",
        }

    return {
        "decision": "GO",
        "confidence": 0.7,
        "reason": "No hard blockers detected in document",
    }


def build_response(decision_obj, facts):
    bid_due_evidence = []
    if facts.get("bid_due") is not None:
        bid_due_evidence = facts["bid_due"].get("evidence", [])

    bond_evidence = facts.get("bond_evidence", [])

    return {
        "decision": decision_obj["decision"],
        "confidence": decision_obj["confidence"],
        "reasons": [
            {
                "text": decision_obj["reason"],
                "evidence": bid_due_evidence + bond_evidence,
            }
        ],
        "facts": facts,
    }


def run_go_no_go_pipeline(pdf_bytes: bytes) -> dict:
    pages = extract_pages(pdf_bytes)
    chunks = chunk_pages(pages)
    facts = extract_core_facts(chunks)
    decision = decide_go_no_go(facts)
    return build_response(decision, facts)
