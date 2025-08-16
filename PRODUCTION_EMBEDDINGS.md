# Production Embeddings Strategy for Vercel Deployment

## Problem
The current embeddings service loads `sentence-transformers/all-MiniLM-L6-v2` in-process, which will exceed Vercel's 50MB deployment size limit and increase cold start times substantially.

## Current Implementation
```python
# src/services/embeddings.py - Current local model
from sentence_transformers import SentenceTransformer

class EmbeddingsService:
    def __init__(self):
        self.model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
```

## Recommended Production Strategies

### Strategy 1: OpenAI Embeddings API (Recommended)
```python
# src/services/embeddings_openai.py
import openai
from typing import List
import asyncio
from functools import lru_cache

class OpenAIEmbeddingsService:
    def __init__(self, api_key: str):
        self.client = openai.AsyncOpenAI(api_key=api_key)
        
    async def get_embedding(self, text: str) -> List[float]:
        """Get embedding using OpenAI's text-embedding-3-small model."""
        response = await self.client.embeddings.create(
            model="text-embedding-3-small",
            input=text,
            encoding_format="float"
        )
        return response.data[0].embedding
    
    async def get_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings for multiple texts efficiently."""
        response = await self.client.embeddings.create(
            model="text-embedding-3-small",
            input=texts,
            encoding_format="float"
        )
        return [data.embedding for data in response.data]

# Environment variables needed:
# OPENAI_API_KEY=your_openai_api_key
```

### Strategy 2: HuggingFace Inference API
```python
# src/services/embeddings_hf.py
import httpx
from typing import List
import asyncio

class HuggingFaceEmbeddingsService:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api-inference.huggingface.co/pipeline/feature-extraction"
        self.model = "sentence-transformers/all-MiniLM-L6-v2"
        
    async def get_embedding(self, text: str) -> List[float]:
        """Get embedding using HuggingFace Inference API."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/{self.model}",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={"inputs": text}
            )
            response.raise_for_status()
            return response.json()

# Environment variables needed:
# HF_API_KEY=your_huggingface_api_token
```

### Strategy 3: Cached External Service with Fallback
```python
# src/services/embeddings_cached.py
from typing import List, Optional
import hashlib
import json
from supabase import Client

class CachedEmbeddingsService:
    def __init__(self, supabase: Client, external_service):
        self.supabase = supabase
        self.external_service = external_service
        
    def _cache_key(self, text: str) -> str:
        """Generate cache key from text."""
        return hashlib.sha256(text.encode()).hexdigest()
    
    async def get_embedding(self, text: str) -> List[float]:
        """Get embedding with caching to reduce API calls."""
        cache_key = self._cache_key(text)
        
        # Try cache first
        cached = self.supabase.table("embedding_cache").select("embedding").eq("cache_key", cache_key).execute()
        if cached.data:
            return json.loads(cached.data[0]["embedding"])
        
        # Get from external service
        embedding = await self.external_service.get_embedding(text)
        
        # Cache for future use
        self.supabase.table("embedding_cache").insert({
            "cache_key": cache_key,
            "text": text[:500],  # Store first 500 chars for reference
            "embedding": json.dumps(embedding),
            "model": "text-embedding-3-small"
        }).execute()
        
        return embedding

# SQL to create cache table:
"""
CREATE TABLE embedding_cache (
    id BIGSERIAL PRIMARY KEY,
    cache_key TEXT UNIQUE NOT NULL,
    text TEXT,
    embedding JSONB NOT NULL,
    model TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_embedding_cache_key ON embedding_cache(cache_key);
"""
```

## Migration Plan

### Phase 1: Development Setup
1. Keep current `sentence-transformers` for local development
2. Add environment variable `EMBEDDINGS_PROVIDER` with options: `local`, `openai`, `huggingface`
3. Create factory pattern to select embeddings service

```python
# src/services/embeddings.py - Updated factory
from src.config import get_settings

def get_embeddings_service():
    settings = get_settings()
    
    if settings.embeddings_provider == "openai":
        from .embeddings_openai import OpenAIEmbeddingsService
        return OpenAIEmbeddingsService(settings.openai_api_key)
    
    elif settings.embeddings_provider == "huggingface":
        from .embeddings_hf import HuggingFaceEmbeddingsService
        return HuggingFaceEmbeddingsService(settings.hf_api_key)
    
    else:  # local development
        from .embeddings_local import LocalEmbeddingsService
        return LocalEmbeddingsService()
```

### Phase 2: Production Deployment
1. Set `EMBEDDINGS_PROVIDER=openai` in Vercel environment variables
2. Add `OPENAI_API_KEY` to Vercel environment variables
3. Deploy with `requirements.prod.txt` (no sentence-transformers)
4. Monitor API usage and costs

### Phase 3: Optimization
1. Implement caching to reduce external API calls
2. Add batch processing for multiple embeddings
3. Monitor performance and adjust model choice

## Cost Comparison

### OpenAI text-embedding-3-small
- **Cost**: $0.00002 per 1K tokens
- **Performance**: High quality, fast API
- **Reliability**: 99.9% uptime SLA

### HuggingFace Inference API
- **Cost**: Free tier available, then $0.0005 per request
- **Performance**: Good quality, variable speed
- **Reliability**: 99% uptime (community models)

### Local (Current)
- **Cost**: Zero API costs
- **Performance**: Fast once loaded
- **Reliability**: Depends on deployment
- **Issue**: Exceeds Vercel size limit

## Recommended Implementation Order
1. **Immediate**: OpenAI API (fastest to implement, high quality)
2. **Short-term**: Add caching layer to reduce API costs
3. **Long-term**: Consider dedicated embedding service if volume grows

## Environment Variables for Production
```bash
# Vercel Backend Environment Variables
EMBEDDINGS_PROVIDER=openai
OPENAI_API_KEY=sk-your-api-key-here

# Alternative: HuggingFace
# EMBEDDINGS_PROVIDER=huggingface  
# HF_API_KEY=hf_your-token-here
```