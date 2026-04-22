"""Bid session CRUD — save/load/list bid drafts."""

import json
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import get_db
from models.bid_session import BidSession
from models.user import User
from services.auth import get_current_user

sessions_router = APIRouter(prefix="/sessions", tags=["sessions"])


class SaveSessionRequest(BaseModel):
    tender_name: str
    tender_doc_id: str | None = None
    sections: list = []
    drafts: dict = {}
    status: str = "in_progress"


class UpdateDraftsRequest(BaseModel):
    drafts: dict = {}
    status: str | None = None


@sessions_router.post("")
async def create_session(
    req: SaveSessionRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Create a new bid session."""
    session = BidSession(
        user_id=user.id,
        tender_name=req.tender_name,
        tender_doc_id=req.tender_doc_id,
        sections_json=json.dumps(req.sections),
        drafts_json=json.dumps(req.drafts),
        status=req.status,
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    return {
        "status": "success",
        "session": _serialize(session),
    }


@sessions_router.get("")
async def list_sessions(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """List all bid sessions for the current user."""
    sessions = (
        db.query(BidSession)
        .filter(BidSession.user_id == user.id)
        .order_by(BidSession.updated_at.desc())
        .all()
    )
    return {
        "status": "success",
        "sessions": [_serialize(s) for s in sessions],
    }


@sessions_router.get("/{session_id}")
async def get_session(
    session_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get a bid session by ID."""
    session = db.query(BidSession).filter(
        BidSession.id == session_id, BidSession.user_id == user.id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return {
        "status": "success",
        "session": _serialize(session),
    }


@sessions_router.put("/{session_id}")
async def update_session(
    session_id: int,
    req: UpdateDraftsRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Update drafts for a bid session (autosave)."""
    session = db.query(BidSession).filter(
        BidSession.id == session_id, BidSession.user_id == user.id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    session.drafts_json = json.dumps(req.drafts)
    if req.status:
        session.status = req.status
    db.commit()

    return {"status": "success"}


@sessions_router.delete("/{session_id}")
async def delete_session(
    session_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Delete a bid session."""
    session = db.query(BidSession).filter(
        BidSession.id == session_id, BidSession.user_id == user.id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    db.delete(session)
    db.commit()
    return {"status": "success"}


def _serialize(s: BidSession) -> dict:
    sections = []
    drafts = {}
    try:
        sections = json.loads(s.sections_json) if s.sections_json else []
    except json.JSONDecodeError:
        pass
    try:
        drafts = json.loads(s.drafts_json) if s.drafts_json else {}
    except json.JSONDecodeError:
        pass

    completed = sum(1 for d in drafts.values() if d and d.get("text"))

    return {
        "id": s.id,
        "tender_name": s.tender_name,
        "tender_doc_id": s.tender_doc_id,
        "sections": sections,
        "drafts": drafts,
        "status": s.status,
        "sections_total": len(sections),
        "sections_completed": completed,
        "created_at": str(s.created_at) if s.created_at else None,
        "updated_at": str(s.updated_at) if s.updated_at else None,
    }
