from sqlalchemy import Column, Integer, String, DateTime, JSON, Text
from sqlalchemy.sql import func
from app.db.base import Base


class Bookmark(Base):
    __tablename__ = "bookmarks"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, index=True)
    title = Column(String)
    content = Column(Text)
    processed_content = Column(Text)
    summary = Column(Text)
    meta_data = Column(JSON, default={})
    embedding = Column(Text)  # Store as base64 encoded string
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
