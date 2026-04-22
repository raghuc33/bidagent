import pytest
import fitz
from services.pdf_parser import (
    extract_pages,
    chunk_pages,
    retrieve_chunks,
    extract_core_facts,
    decide_go_no_go,
    run_go_no_go_pipeline,
)


def _make_pdf(texts: list[str]) -> bytes:
    """Create a test PDF with given page texts."""
    doc = fitz.open()
    for text in texts:
        page = doc.new_page()
        page.insert_text((72, 100), text, fontsize=12)
    return doc.tobytes()


def _make_long_pdf() -> bytes:
    """Create a PDF with enough text to pass the scanned PDF check (>500 chars)."""
    doc = fitz.open()
    lines = [
        "REQUEST FOR PROPOSAL",
        "Project: City Hall Renovation Phase 2",
        "Issued by: Department of Public Works, Springfield",
        "RFP Number: DPW-2026-0042",
        "Issue Date: February 1, 2026",
        "Submission Deadline: April 30, 2026 at 5:00 PM EST",
        "All proposals must be delivered to the Office of Procurement,",
        "123 Main Street, Springfield, IL 62701.",
        "Questions regarding this RFP must be submitted in writing",
        "to procurement@springfield.gov no later than March 15, 2026.",
        "The City of Springfield seeks qualified contractors for the",
        "renovation of City Hall, including structural repairs, HVAC",
        "system upgrades, ADA compliance improvements, and interior",
        "modernization. The building was constructed in 1952.",
        "A bid bond of 5% of the total bid amount is required.",
        "The contractor shall provide proof of general liability insurance.",
        "Minimum 10 years of experience in commercial renovation required.",
        "Budget Range: $2,000,000 to $3,500,000.",
        "The project must be completed within 18 months.",
    ]
    page = doc.new_page()
    y = 80
    for line in lines:
        page.insert_text((72, y), line, fontsize=11)
        y += 20
    return doc.tobytes()


def test_extract_pages_valid_pdf():
    pdf = _make_long_pdf()
    pages = extract_pages(pdf)
    assert len(pages) >= 1
    assert pages[0]["page"] == 1
    assert len(pages[0]["text"]) > 0


def test_extract_pages_scanned_pdf():
    """PDF with very little text should raise SCANNED_PDF."""
    pdf = _make_pdf(["Hi"])
    with pytest.raises(ValueError, match="SCANNED_PDF"):
        extract_pages(pdf)


def test_chunk_pages():
    pages = [{"page": 1, "text": "A" * 5000}, {"page": 2, "text": "B" * 3000}]
    chunks = chunk_pages(pages)
    assert len(chunks) >= 2  # First page should split into 2 chunks
    assert all("chunk_id" in c for c in chunks)
    assert all("page" in c for c in chunks)


def test_retrieve_chunks():
    chunks = [
        {"text": "The deadline is April 30, 2026", "page": 1, "chunk_id": "c1"},
        {"text": "No relevant info here", "page": 2, "chunk_id": "c2"},
        {"text": "A bid bond of 5% is required", "page": 3, "chunk_id": "c3"},
    ]
    results = retrieve_chunks(chunks, ["deadline", "due"])
    assert len(results) == 1
    assert results[0]["chunk_id"] == "c1"


def test_decide_go_no_go_missing_due_date():
    facts = {"bid_due": None, "bond_required": False, "mandatory_items": []}
    decision = decide_go_no_go(facts)
    assert decision["decision"] == "NEEDS_INFO"
    assert decision["confidence"] == 0.45


def test_decide_go_no_go_bond_required():
    facts = {"bid_due": {"value": "2026-04-30"}, "bond_required": True, "mandatory_items": []}
    decision = decide_go_no_go(facts)
    assert decision["decision"] == "NEEDS_INFO"
    assert decision["confidence"] == 0.55


def test_decide_go_no_go_all_clear():
    facts = {"bid_due": {"value": "2026-04-30"}, "bond_required": False, "mandatory_items": []}
    decision = decide_go_no_go(facts)
    assert decision["decision"] == "GO"
    assert decision["confidence"] == 0.7


def test_run_pipeline():
    pdf = _make_long_pdf()
    result = run_go_no_go_pipeline(pdf)
    assert "decision" in result
    assert result["decision"] in ("GO", "NO_GO", "NEEDS_INFO")
    assert "confidence" in result
    assert "reasons" in result
