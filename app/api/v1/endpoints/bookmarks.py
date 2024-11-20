from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.base import get_db
from app.models.bookmark import Bookmark
from app.schemas.bookmark import BookmarkCreate, BookmarkInDB, SearchQuery, SearchResult
from app.services.search_service import SearchService

router = APIRouter()
search_service = SearchService()

@router.post("/", response_model=BookmarkInDB)
async def create_bookmark(bookmark: BookmarkCreate, db: AsyncSession = Depends(get_db)):
    """Yeni bir bookmark oluştur"""
    db_bookmark = Bookmark(
        url=str(bookmark.url),
        title=bookmark.title,
        content=bookmark.content
    )
    
    # Vektör gömme oluştur
    if bookmark.content:
        embedding = search_service._encode_text(bookmark.content)
        db_bookmark.embedding = search_service._encode_embedding(embedding)
    
    db.add(db_bookmark)
    await db.commit()
    await db.refresh(db_bookmark)
    return db_bookmark

@router.get("/", response_model=List[BookmarkInDB])
async def read_bookmarks(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    """Bookmarkları listele"""
    result = await db.execute(select(Bookmark).offset(skip).limit(limit))
    bookmarks = result.scalars().all()
    return bookmarks

@router.get("/{bookmark_id}", response_model=BookmarkInDB)
async def read_bookmark(bookmark_id: int, db: AsyncSession = Depends(get_db)):
    """Belirli bir bookmark'ı getir"""
    result = await db.execute(select(Bookmark).filter(Bookmark.id == bookmark_id))
    bookmark = result.scalar_one_or_none()
    
    if bookmark is None:
        raise HTTPException(status_code=404, detail="Bookmark not found")
        
    return bookmark

@router.post("/search", response_model=List[SearchResult])
async def search_bookmarks(query: SearchQuery, db: AsyncSession = Depends(get_db)):
    """Bookmarklarda arama yap"""
    results = await search_service.search(query, db)
    return results
