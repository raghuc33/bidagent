from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from database import Base


class BidSession(Base):
    __tablename__ = "bid_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    tender_name = Column(String, nullable=False)
    tender_doc_id = Column(String)  # ChromaDB doc ID
    sections_json = Column(Text)    # JSON: extracted sections list
    drafts_json = Column(Text)      # JSON: {section_id: {text, sources, score, wordCount}}
    status = Column(String, default="in_progress")  # in_progress, completed
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
