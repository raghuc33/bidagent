from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from sqlalchemy.sql import func
from database import Base


class TenderSession(Base):
    __tablename__ = "tender_sessions"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    decision = Column(String)  # GO / NO_GO / NEEDS_INFO
    confidence = Column(Float)
    facts_json = Column(Text)  # JSON blob of extracted facts
    created_at = Column(DateTime, server_default=func.now())
