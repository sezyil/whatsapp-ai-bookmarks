from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from twilio.rest import Client
from twilio.request_validator import RequestValidator
from app.core.config import get_settings
from app.db.base import get_db
from app.schemas.bookmark import BookmarkCreate
from app.api.v1.endpoints.bookmarks import create_bookmark
import re
from urllib.parse import urlparse

router = APIRouter()
settings = get_settings()

# Twilio istemcisini oluştur
client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
validator = RequestValidator(settings.TWILIO_AUTH_TOKEN)

def validate_twilio_request(request: Request):
    """Twilio webhook isteğini doğrula"""
    # Twilio imza doğrulaması
    signature = request.headers.get("X-Twilio-Signature", "")
    url = str(request.url)
    
    if not validator.validate(url, await request.form(), signature):
        raise HTTPException(status_code=403, detail="Invalid Twilio signature")

def extract_url_from_message(message: str) -> str:
    """Mesaj içindeki URL'yi çıkar"""
    url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    urls = re.findall(url_pattern, message)
    return urls[0] if urls else None

@router.post("/webhook")
async def whatsapp_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """WhatsApp webhook endpoint'i"""
    # İsteği doğrula
    validate_twilio_request(request)
    
    # Form verilerini al
    form_data = await request.form()
    message = form_data.get("Body", "").strip()
    from_number = form_data.get("From", "")
    
    # URL'yi çıkar
    url = extract_url_from_message(message)
    if not url:
        # URL bulunamadıysa hata mesajı gönder
        await send_whatsapp_message(
            to=from_number,
            message="❌ URL bulunamadı. Lütfen geçerli bir URL paylaşın."
        )
        return {"status": "error", "message": "No URL found"}
    
    try:
        # Bookmark oluştur
        bookmark_data = BookmarkCreate(url=url)
        bookmark = await create_bookmark(bookmark_data, db)
        
        # Başarı mesajı gönder
        await send_whatsapp_message(
            to=from_number,
            message=f"✅ Bookmark başarıyla kaydedildi!\n\n🔗 {url}\n\n🔍 '/ara' komutuyla bookmarklarınızda arama yapabilirsiniz."
        )
        
        return {"status": "success", "bookmark_id": bookmark.id}
        
    except Exception as e:
        # Hata durumunda kullanıcıya bilgi ver
        await send_whatsapp_message(
            to=from_number,
            message=f"❌ Bookmark kaydedilirken bir hata oluştu: {str(e)}"
        )
        raise HTTPException(status_code=500, detail=str(e))

async def send_whatsapp_message(to: str, message: str):
    """WhatsApp mesajı gönder"""
    try:
        client.messages.create(
            from_=f"whatsapp:{settings.TWILIO_PHONE_NUMBER}",
            body=message,
            to=to
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send WhatsApp message: {str(e)}")
