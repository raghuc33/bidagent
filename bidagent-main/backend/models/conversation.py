from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.sql import func
from database import Base


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, nullable=False, index=True)
    section_id = Column(String, nullable=False, index=True)
    role = Column(String, nullable=False)  # user, assistant
    content = Column(Text)
    tool_calls_json = Column(Text)  # JSON array of tool call summaries
    updated_draft = Column(Text)  # draft text if the agent updated it
    created_at = Column(DateTime, server_default=func.now())
