"""Chat API — agentic conversation for bid section refinement."""

import json
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import get_db
from models.conversation import Conversation
from services.agent import run_agent_turn
from services.auth import get_current_user

chat_router = APIRouter(prefix="/chat", tags=["chat"])


class ChatMessageRequest(BaseModel):
    session_id: str
    section_id: str
    message: str
    current_draft: str = ""
    section_title: str = ""
    section_description: str = ""
    doc_id: str | None = None


@chat_router.post("/message")
async def send_message(
    req: ChatMessageRequest,
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    """Send a message to the bid-writing agent and get a response."""

    # Load conversation history from DB
    history_rows = (
        db.query(Conversation)
        .filter(
            Conversation.session_id == req.session_id,
            Conversation.section_id == req.section_id,
        )
        .order_by(Conversation.created_at)
        .all()
    )

    conversation_history = []
    for row in history_rows:
        conversation_history.append({"role": row.role, "content": row.content or ""})

    # Add the new user message
    conversation_history.append({"role": "user", "content": req.message})

    # Save user message to DB
    db.add(Conversation(
        session_id=req.session_id,
        section_id=req.section_id,
        role="user",
        content=req.message,
    ))
    db.commit()

    # Run agent turn
    try:
        result = await run_agent_turn(
            conversation_history=conversation_history,
            section_title=req.section_title,
            section_description=req.section_description,
            current_draft=req.current_draft,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")

    # Save assistant response to DB
    db.add(Conversation(
        session_id=req.session_id,
        section_id=req.section_id,
        role="assistant",
        content=result["text"],
        tool_calls_json=json.dumps(result["tool_calls"]) if result["tool_calls"] else None,
        updated_draft=result.get("updated_draft"),
    ))
    db.commit()

    return {
        "status": "success",
        "response": {
            "text": result["text"],
            "updated_draft": result.get("updated_draft"),
            "tool_calls": result["tool_calls"],
            "word_count": len(result["updated_draft"].split()) if result.get("updated_draft") else None,
        },
    }


@chat_router.get("/history/{session_id}/{section_id}")
async def get_history(
    session_id: str,
    section_id: str,
    db: Session = Depends(get_db),
    _user=Depends(get_current_user),
):
    """Retrieve conversation history for a section."""
    rows = (
        db.query(Conversation)
        .filter(
            Conversation.session_id == session_id,
            Conversation.section_id == section_id,
        )
        .order_by(Conversation.created_at)
        .all()
    )

    messages = []
    for row in rows:
        msg = {
            "role": row.role,
            "content": row.content or "",
            "updated_draft": row.updated_draft,
            "tool_calls": json.loads(row.tool_calls_json) if row.tool_calls_json else [],
            "created_at": str(row.created_at) if row.created_at else None,
        }
        messages.append(msg)

    return {"status": "success", "messages": messages}
