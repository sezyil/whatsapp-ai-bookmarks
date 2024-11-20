from pydantic import BaseModel, HttpUrl
from typing import Optional, Dict, Any, List
from datetime import datetime


class BookmarkBase(BaseModel):
    url: HttpUrl
    title: Optional[str] = None
    content: Optional[str] = None


class BookmarkCreate(BookmarkBase):
    pass


class BookmarkUpdate(BookmarkBase):
    meta_data: Optional[Dict[str, Any]] = None


class BookmarkInDB(BookmarkBase):
    id: int
    processed_content: Optional[str] = None
    summary: Optional[str] = None
    meta_data: Dict[str, Any]
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SearchQuery(BaseModel):
    query: str
    filters: Optional[Dict[str, Any]] = None
    date_range: Optional[Dict[str, str]] = None
    tags: Optional[List[str]] = None
    limit: Optional[int] = 10


class SearchResult(BaseModel):
    id: int
    url: HttpUrl
    title: str
    summary: Optional[str]
    relevance_score: float
    meta_data: Dict[str, Any]

    class Config:
        from_attributes = True
