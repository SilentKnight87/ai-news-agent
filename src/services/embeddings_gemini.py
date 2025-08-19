"""
Gemini Embeddings service for production deployment.

This module provides embeddings functionality using Google's Gemini text-embedding-004 API,
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


class GeminiEmbeddingsService:
    """
    Production embeddings service using Google's Gemini text-embedding-004 API.
    
    This service is optimized for Vercel deployment as it doesn't require
    heavy ML dependencies and provides high-quality embeddings.
    """

    def __init__(self, api_key: str):
        """
        Initialize the Gemini embeddings service.
        
        Args:
            api_key: Google Gemini API key for authentication.
        """
        self.api_key = api_key
        self.model_name = "text-embedding-004"
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"
        
        # Implement size-limited LRU cache (max 1000 entries)
        self._cache = LRUCache(maxsize=1000)
        
        logger.info(f"Gemini embeddings service initialized with model: {self.model_name}")

    async def generate_embedding(self, text: str, use_cache: bool = True) -> List[float]:
        """
        Generate embedding for a single text using Gemini API.

        Args:
            text: Text to generate embedding for.
            use_cache: Whether to use cached embeddings.

        Returns:
            List[float]: 768-dimensional embedding vector (configurable, default 3072).
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")

        # Normalize text for caching
        normalized_text = text.strip()

        # Check cache first
        if use_cache and normalized_text in self._cache:
            logger.debug("Using cached embedding")
            return self._cache[normalized_text]

        # Generate embedding via API
        embedding = await self._call_gemini_api([text])
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
        Generate embeddings for multiple texts efficiently.

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
                # Return zero vector for empty texts (using 384 to match database schema)
                results[i] = [0.0] * 384  # Match database vector(384) definition
                continue

            normalized_text = text.strip()

            if use_cache and normalized_text in self._cache:
                results[i] = self._cache[normalized_text]
            else:
                texts_to_process.append((i, text, normalized_text))

        # Process remaining texts individually (Gemini doesn't support batch requests)
        for original_index, text, normalized_text in texts_to_process:
            try:
                embedding = await self.generate_embedding(text, use_cache=False)
                results[original_index] = embedding
                
                if use_cache:
                    self._cache[normalized_text] = embedding
                    
            except Exception as e:
                logger.error(f"Failed to generate embedding for text {original_index}: {e}")
                results[original_index] = [0.0] * 384  # Fallback to zero vector

        # Convert None results to zero vectors
        final_results = []
        for result in results:
            if result is not None:
                final_results.append(result)
            else:
                final_results.append([0.0] * 384)

        logger.debug(f"Generated {len(final_results)} embeddings")
        return final_results

    async def _call_gemini_api(self, texts: List[str]) -> List[List[float]]:
        """
        Call Gemini embeddings API.
        
        Args:
            texts: List of texts to process.
            
        Returns:
            List[List[float]]: List of embedding vectors.
            
        Raises:
            Exception: If API call fails after retries.
        """
        results = []
        
        # Process each text individually
        for text in texts:
            payload = {
                "model": f"models/{self.model_name}",
                "content": {
                    "parts": [{"text": text}]
                },
                "taskType": "SEMANTIC_SIMILARITY",
                "outputDimensionality": 384
            }
            
            url = f"{self.base_url}/{self.model_name}:embedContent?key={self.api_key}"
            
            headers = {
                "Content-Type": "application/json"
            }

            # Retry logic with exponential backoff
            max_retries = 3
            base_delay = 1.0

            for attempt in range(max_retries):
                try:
                    async with httpx.AsyncClient(timeout=30.0) as client:
                        response = await client.post(
                            url,
                            json=payload,
                            headers=headers
                        )
                        
                        if response.status_code == 200:
                            data = response.json()
                            # Gemini API returns embedding in 'embedding' field with 'values' array
                            embedding = data["embedding"]["values"]
                            results.append(embedding)
                            break
                        
                        elif response.status_code == 429:  # Rate limit
                            if attempt < max_retries - 1:
                                delay = base_delay * (2 ** attempt)
                                logger.warning(f"Rate limited, retrying in {delay}s...")
                                await asyncio.sleep(delay)
                                continue
                        
                        elif response.status_code == 400:  # Bad Request
                            logger.error(f"Bad Request (400): {response.text}")
                            logger.error(f"Request payload: {payload}")
                            if attempt < max_retries - 1:
                                delay = base_delay * (2 ** attempt)
                                logger.warning(f"API error: Client error '400 Bad Request' for url '{url}', retrying in {delay}s...")
                                await asyncio.sleep(delay)
                                continue
                        
                        # Handle other errors
                        logger.error(f"HTTP {response.status_code}: {response.text}")
                        response.raise_for_status()
                        
                except httpx.TimeoutException:
                    if attempt < max_retries - 1:
                        delay = base_delay * (2 ** attempt)
                        logger.warning(f"API timeout, retrying in {delay}s...")
                        await asyncio.sleep(delay)
                        continue
                    else:
                        raise Exception("Gemini API timeout after retries")
                
                except Exception as e:
                    if attempt < max_retries - 1:
                        delay = base_delay * (2 ** attempt)
                        logger.warning(f"API error: {e}, retrying in {delay}s...")
                        await asyncio.sleep(delay)
                        continue
                    else:
                        raise Exception(f"Gemini API call failed: {e}")

        return results

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

        # Calculate dot product and magnitudes
        dot_product = sum(a * b for a, b in zip(embedding1, embedding2))
        magnitude1 = sum(a * a for a in embedding1) ** 0.5
        magnitude2 = sum(b * b for b in embedding2) ** 0.5
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        # Calculate cosine similarity
        similarity = dot_product / (magnitude1 * magnitude2)
        
        # Clamp to valid range due to floating point precision
        return max(-1.0, min(1.0, similarity))

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
        logger.info("Gemini embedding cache cleared")

    def get_model_info(self) -> dict:
        """
        Get information about the embedding model.

        Returns:
            Dict: Model information.
        """
        return {
            "model_name": self.model_name,
            "embedding_dimension": 384,  # Match database vector(384) definition
            "max_embedding_dimension": 3072,
            "cache_size": self.get_cache_size(),
            "provider": "gemini",
            "api_base": self.base_url
        }