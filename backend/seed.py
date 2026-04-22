import json
import os
import threading
import time
from database import SessionLocal
from models.user import User
from models.session import TenderSession
from services.auth import hash_password

DUMP_FILE = os.path.join(os.path.dirname(__file__), "seed_data.json")
DUMP_INTERVAL = 300  # 5 minutes


def dump_db():
    """Dump all DB tables to JSON."""
    db = SessionLocal()
    try:
        users = []
        for u in db.query(User).all():
            users.append({
                "id": u.id,
                "email": u.email,
                "hashed_password": u.hashed_password,
                "name": u.name,
                "created_at": str(u.created_at) if u.created_at else None,
            })

        sessions = []
        for s in db.query(TenderSession).all():
            sessions.append({
                "id": s.id,
                "filename": s.filename,
                "decision": s.decision,
                "confidence": s.confidence,
                "facts_json": s.facts_json,
                "created_at": str(s.created_at) if s.created_at else None,
            })

        data = {"users": users, "tender_sessions": sessions}

        with open(DUMP_FILE, "w") as f:
            json.dump(data, f, indent=2)
    finally:
        db.close()


def restore_db():
    """Restore DB from JSON dump on startup."""
    if not os.path.exists(DUMP_FILE):
        return

    with open(DUMP_FILE) as f:
        data = json.load(f)

    db = SessionLocal()
    try:
        for u in data.get("users", []):
            if db.query(User).filter(User.email == u["email"]).first():
                continue
            # If we have a pre-hashed password use it, otherwise hash the plain one
            hashed = u.get("hashed_password") or hash_password(u["password"])
            db.add(User(
                email=u["email"],
                hashed_password=hashed,
                name=u["name"],
            ))

        for s in data.get("tender_sessions", []):
            if db.query(TenderSession).filter(TenderSession.id == s["id"]).first():
                continue
            db.add(TenderSession(
                filename=s["filename"],
                decision=s.get("decision"),
                confidence=s.get("confidence"),
                facts_json=s.get("facts_json"),
            ))

        db.commit()
    finally:
        db.close()


def _dump_loop():
    while True:
        time.sleep(DUMP_INTERVAL)
        try:
            dump_db()
        except Exception as e:
            print(f"[seed] dump failed: {e}")


def start_dump_scheduler():
    """Start background thread that dumps DB to JSON every 5 minutes."""
    t = threading.Thread(target=_dump_loop, daemon=True)
    t.start()
