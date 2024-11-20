from fastapi import APIRouter
from app.api.v1.endpoints import bookmarks, whatsapp

api_router = APIRouter()
api_router.include_router(bookmarks.router, prefix="/bookmarks", tags=["bookmarks"])
api_router.include_router(whatsapp.router, prefix="/whatsapp", tags=["whatsapp"])
