"""
OpenAI Embeddings service for production deployment.

This module provides embeddings functionality using OpenAI's text-embedding-3-small API,
which is production-ready and doesn't require heavy local ML models.
"""

import asyncio
import logging
from typing import List
from functools import lru_cache

import httpx
from cachetools import LRUCache

from ..config import get_settings

logger = logging.getLogger(__name__)


class OpenAIEmbeddingsService:
    """
    Production embeddings service using OpenAI's text-embedding-3-small API.
    
    This service is optimized for Vercel deployment as it doesn't require
    heavy ML dependencies and provides consistent, high-quality embeddings.
    """

    def __init__(self, api_key: str):
        """
        Initialize the OpenAI embeddings service.
        
        Args:
            api_key: OpenAI API key for authentication.
        """
        self.api_key = api_key
        self.model_name = "text-embedding-3-small"
        self.base_url = "https://api.openai.com/v1/embeddings"
        self.max_tokens = 8191  # Model limit for text-embedding-3-small
        
        # Implement size-limited LRU cache (max 1000 entries)
        self._cache = LRUCache(maxsize=1000)
        
        logger.info(f"OpenAI embeddings service initialized with model: {self.model_name}")

    async def generate_embedding(self, text: str, use_cache: bool = True) -> List[float]:
        """
        Generate embedding for a single text using OpenAI API.

        Args:
            text: Text to generate embedding for.
            use_cache: Whether to use cached embeddings.

        Returns:
            List[float]: 1536-dimensional embedding vector.
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")

        # Normalize text for caching
        normalized_text = text.strip()

        # Check cache first
        if use_cache and normalized_text in self._cache:
            logger.debug("Using cached embedding")
            return self._cache[normalized_text]

        # Truncate text if too long
        if len(text) > self.max_tokens * 4:  # Rough estimate: 4 chars per token
            text = text[:self.max_tokens * 4] + "..."

        # Generate embedding via API
        embedding = await self._call_openai_api([text])
        result = embedding[0]

        # Cache the result
        if use_cache:
            self._cache[normalized_text] = result

        return result

    async def generate_embeddings_batch(
        self,
        texts: List[str],
        use_cache: bool = True
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts efficiently using batch API.

        Args:
            texts: List of texts to generate embeddings for.
            use_cache: Whether to use cached embeddings.

        Returns:
            List[List[float]]: List of embedding vectors.
        """
        if not texts:
            return []

        logger.debug(f"Generating embeddings for {len(texts)} texts")

        # Filter out empty texts and check cache
        texts_to_process = []
        results = [None] * len(texts)

        for i, text in enumerate(texts):
            if not text or not text.strip():
                # Return zero vector for empty texts
                results[i] = [0.0] * 1536  # text-embedding-3-small dimension
                continue

            normalized_text = text.strip()

            if use_cache and normalized_text in self._cache:
                results[i] = self._cache[normalized_text]
            else:
                texts_to_process.append((i, text, normalized_text))

        # Process remaining texts in batches (OpenAI supports up to 2048 inputs)
        if texts_to_process:
            batch_size = 50  # Conservative batch size for API stability
            
            for i in range(0, len(texts_to_process), batch_size):
                batch = texts_to_process[i:i + batch_size]
                batch_texts = [item[1] for item in batch]
                
                # Truncate long texts
                processed_texts = []
                for text in batch_texts:
                    if len(text) > self.max_tokens * 4:
                        text = text[:self.max_tokens * 4] + "..."
                    processed_texts.append(text)

                # Call API for batch
                batch_embeddings = await self._call_openai_api(processed_texts)

                # Store results and cache
                for j, (original_index, _, normalized_text) in enumerate(batch):
                    embedding = batch_embeddings[j]
                    results[original_index] = embedding

                    if use_cache:
                        self._cache[normalized_text] = embedding

        # Convert None results to zero vectors
        final_results = []
        for result in results:
            if result is not None:
                final_results.append(result)
            else:
                final_results.append([0.0] * 1536)

        logger.debug(f"Generated {len(final_results)} embeddings")
        return final_results

    async def _call_openai_api(self, texts: List[str]) -> List[List[float]]:
        """
        Call OpenAI embeddings API.
        
        Args:
            texts: List of texts to process.
            
        Returns:
            List[List[float]]: List of embedding vectors.
            
        Raises:
            Exception: If API call fails after retries.
        """
        payload = {
            "model": self.model_name,
            "input": texts,
            "encoding_format": "float"
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        # Retry logic with exponential backoff
        max_retries = 3
        base_delay = 1.0

        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(
                        self.base_url,
                        json=payload,
                        headers=headers
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        return [item["embedding"] for item in data["data"]]
                    
                    elif response.status_code == 429:  # Rate limit
                        if attempt < max_retries - 1:
                            delay = base_delay * (2 ** attempt)
                            logger.warning(f"Rate limited, retrying in {delay}s...")
                            await asyncio.sleep(delay)
                            continue
                    
                    # Handle other errors
                    response.raise_for_status()
                    
            except httpx.TimeoutException:
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)
                    logger.warning(f"API timeout, retrying in {delay}s...")
                    await asyncio.sleep(delay)
                    continue
                else:
                    raise Exception("OpenAI API timeout after retries")
            
            except Exception as e:
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)
                    logger.warning(f"API error: {e}, retrying in {delay}s...")
                    await asyncio.sleep(delay)
                    continue
                else:
                    raise Exception(f"OpenAI API call failed: {e}")

        raise Exception("OpenAI API call failed after all retries")

    def cosine_similarity(
        self,
        embedding1: List[float],
        embedding2: List[float]
    ) -> float:
        """
        Calculate cosine similarity between two embeddings.

        Args:
            embedding1: First embedding vector.
            embedding2: Second embedding vector.

        Returns:
            float: Cosine similarity score (-1 to 1).
        """
        if len(embedding1) != len(embedding2):
            raise ValueError("Embeddings must have the same dimension")

        # OpenAI embeddings are already normalized
        dot_product = sum(a * b for a, b in zip(embedding1, embedding2))
        
        # Clamp to valid range due to floating point precision
        return max(-1.0, min(1.0, dot_product))

    async def generate_article_embedding(self, article_title: str, article_content: str) -> List[float]:
        """
        Generate embedding for an article using title and content.

        Args:
            article_title: Article title.
            article_content: Article content.

        Returns:
            List[float]: Article embedding.
        """
        # Combine title and content with appropriate weighting
        # Title is more important for similarity, so weight it more
        combined_text = f"{article_title}. {article_title}. {article_content}"

        return await self.generate_embedding(combined_text)

    def get_cache_size(self) -> int:
        """
        Get the number of cached embeddings.

        Returns:
            int: Number of cached embeddings.
        """
        return len(self._cache)

    def clear_cache(self) -> None:
        """Clear the embedding cache."""
        self._cache.clear()
        logger.info("OpenAI embedding cache cleared")

    def get_model_info(self) -> dict:
        """
        Get information about the embedding model.

        Returns:
            Dict: Model information.
        """
        return {
            "model_name": self.model_name,
            "embedding_dimension": 1536,
            "cache_size": self.get_cache_size(),
            "provider": "openai",
            "max_tokens": self.max_tokens
        }