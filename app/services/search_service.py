import json
import numpy as np
import faiss
import base64
from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer
import aiohttp
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import get_settings
from app.models.bookmark import Bookmark
from app.schemas.bookmark import SearchQuery, SearchResult

settings = get_settings()

class SearchService:
    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.index = faiss.IndexFlatL2(384)  # Dimension of all-MiniLM-L6-v2 embeddings
        self.xai_api_key = settings.XAI_API_KEY
        self.xai_model = settings.XAI_MODEL

    async def _get_grok_analysis(self, query: str) -> Dict[str, Any]:
        """X.AI Grok API'sini kullanarak sorguyu analiz et"""
        headers = {
            "Authorization": f"Bearer {self.xai_api_key}",
            "Content-Type": "application/json"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.x.ai/v1/query",
                headers=headers,
                json={
                    "model": self.xai_model,
                    "messages": [
                        {"role": "system", "content": "Analyze the search query and extract key information."},
                        {"role": "user", "content": query}
                    ]
                }
            ) as response:
                return await response.json()

    def _encode_text(self, text: str) -> np.ndarray:
        """Metni vektör gömmeye dönüştür"""
        return self.model.encode([text])[0]

    def _decode_embedding(self, embedding_str: str) -> np.ndarray:
        """Base64 kodlu gömmeyi numpy dizisine dönüştür"""
        embedding_bytes = base64.b64decode(embedding_str)
        return np.frombuffer(embedding_bytes, dtype=np.float32)

    def _encode_embedding(self, embedding: np.ndarray) -> str:
        """Numpy dizisini base64'e kodla"""
        return base64.b64encode(embedding.astype(np.float32).tobytes()).decode()

    async def _semantic_search(self, query: str, bookmarks: List[Bookmark]) -> List[Dict[Any, Any]]:
        """Anlamsal arama gerçekleştir"""
        if not bookmarks:
            return []

        # Sorgu vektörünü oluştur
        query_vector = self._encode_text(query)
        
        # Bookmark vektörlerini al
        bookmark_vectors = []
        for bookmark in bookmarks:
            if bookmark.embedding:
                bookmark_vectors.append(self._decode_embedding(bookmark.embedding))
        
        if not bookmark_vectors:
            return []
            
        # FAISS indeksini yeniden oluştur
        self.index = faiss.IndexFlatL2(384)
        self.index.add(np.array(bookmark_vectors))
        
        # En yakın komşuları bul
        D, I = self.index.search(query_vector.reshape(1, -1), len(bookmarks))
        
        # Sonuçları hazırla
        results = []
        for idx, (distance, orig_idx) in enumerate(zip(D[0], I[0])):
            if idx >= len(bookmarks):
                break
                
            bookmark = bookmarks[orig_idx]
            meta_data = json.loads(bookmark.meta_data) if bookmark.meta_data else {}
            
            results.append({
                "id": bookmark.id,
                "url": str(bookmark.url),
                "title": bookmark.title,
                "summary": bookmark.summary,
                "relevance_score": 1 / (1 + distance),  # Convert distance to similarity score
                "meta_data": meta_data
            })
            
        return sorted(results, key=lambda x: x["relevance_score"], reverse=True)

    async def _tag_search(self, tags: List[str], bookmarks: List[Bookmark]) -> List[Dict[Any, Any]]:
        """Etiket bazlı arama"""
        results = []
        
        for bookmark in bookmarks:
            meta_data = json.loads(bookmark.meta_data) if bookmark.meta_data else {}
            bookmark_tags = meta_data.get("tags", [])
            
            # Etiket eşleşmesi kontrol et
            matching_tags = set(tags) & set(bookmark_tags)
            if matching_tags:
                results.append({
                    "id": bookmark.id,
                    "url": str(bookmark.url),
                    "title": bookmark.title,
                    "summary": bookmark.summary,
                    "relevance_score": len(matching_tags) / len(tags),
                    "meta_data": meta_data
                })
                
        return sorted(results, key=lambda x: x["relevance_score"], reverse=True)

    async def _date_search(self, date_range: Dict[str, str], bookmarks: List[Bookmark]) -> List[Dict[Any, Any]]:
        """Tarih aralığı bazlı arama"""
        from datetime import datetime
        
        results = []
        start_date = datetime.fromisoformat(date_range["start"])
        end_date = datetime.fromisoformat(date_range["end"])
        
        for bookmark in bookmarks:
            if start_date <= bookmark.created_at <= end_date:
                meta_data = json.loads(bookmark.meta_data) if bookmark.meta_data else {}
                results.append({
                    "id": bookmark.id,
                    "url": str(bookmark.url),
                    "title": bookmark.title,
                    "summary": bookmark.summary,
                    "relevance_score": 1.0,  # Tarih aralığında olan tüm sonuçlar eşit öneme sahip
                    "meta_data": meta_data
                })
                
        return results

    async def search(self, query: SearchQuery, db: AsyncSession) -> List[SearchResult]:
        """Ana arama fonksiyonu"""
        # Tüm bookmarkları getir
        result = await db.execute(select(Bookmark))
        bookmarks = result.scalars().all()
        
        if not bookmarks:
            return []
            
        # Grok API'den sorgu analizi al
        analysis = await self._get_grok_analysis(query.query)
        
        # Farklı arama stratejilerini uygula
        results = []
        
        # 1. Anlamsal arama
        semantic_results = await self._semantic_search(query.query, bookmarks)
        results.extend(semantic_results)
        
        # 2. Etiket araması
        if query.tags:
            tag_results = await self._tag_search(query.tags, bookmarks)
            results.extend(tag_results)
            
        # 3. Tarih aralığı araması
        if query.date_range:
            date_results = await self._date_search(query.date_range, bookmarks)
            results.extend(date_results)
            
        # Sonuçları birleştir ve sırala
        unique_results = {}
        for result in results:
            if result["id"] not in unique_results:
                unique_results[result["id"]] = result
            else:
                # Var olan sonucun relevance_score'unu güncelle
                unique_results[result["id"]]["relevance_score"] = max(
                    unique_results[result["id"]]["relevance_score"],
                    result["relevance_score"]
                )
                
        # Son sonuçları oluştur
        final_results = list(unique_results.values())
        final_results.sort(key=lambda x: x["relevance_score"], reverse=True)
        
        # Limit uygula
        return [SearchResult(**result) for result in final_results[:query.limit]]
