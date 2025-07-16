"""
Embeddings service for generating vector representations of articles.

This module provides functionality to generate and cache vector embeddings
using HuggingFace sentence-transformers for semantic similarity search.
"""

import asyncio
import logging
from functools import lru_cache

import numpy as np
from sentence_transformers import SentenceTransformer

from ..config import get_settings

logger = logging.getLogger(__name__)


class EmbeddingsService:
    """
    Service for generating and managing vector embeddings.

    Uses HuggingFace sentence-transformers to generate 384-dimensional
    embeddings for article content using the all-MiniLM-L6-v2 model.
    """

    def __init__(self):
        """Initialize the embeddings service."""
        self.settings = get_settings()
        self.model_name = self.settings.embedding_model
        self.batch_size = self.settings.embedding_batch_size
        self._model: SentenceTransformer | None = None
        self._cache: dict[str, list[float]] = {}

        logger.info(f"Embeddings service initialized with model: {self.model_name}")

    @property
    def model(self) -> SentenceTransformer:
        """
        Lazy-load the sentence transformer model.

        Returns:
            SentenceTransformer: The loaded model.
        """
        if self._model is None:
            logger.info(f"Loading sentence transformer model: {self.model_name}")
            self._model = SentenceTransformer(self.model_name)
            logger.info("Model loaded successfully")

        return self._model

    async def generate_embedding(self, text: str, use_cache: bool = True) -> list[float]:
        """
        Generate embedding for a single text.

        Args:
            text: Text to generate embedding for.
            use_cache: Whether to use cached embeddings.

        Returns:
            List[float]: 384-dimensional embedding vector.
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")

        # Normalize text for caching
        normalized_text = text.strip().lower()

        # Check cache first
        if use_cache and normalized_text in self._cache:
            logger.debug("Using cached embedding")
            return self._cache[normalized_text]

        # Generate embedding in thread pool to avoid blocking
        embedding = await asyncio.get_event_loop().run_in_executor(
            None, self._generate_embedding_sync, text
        )

        # Cache the result
        if use_cache:
            self._cache[normalized_text] = embedding

        return embedding

    def _generate_embedding_sync(self, text: str) -> list[float]:
        """
        Generate embedding synchronously.

        Args:
            text: Text to generate embedding for.

        Returns:
            List[float]: Embedding vector.
        """
        # Truncate text if too long (model has token limits)
        if len(text) > 8000:  # Conservative limit
            text = text[:8000] + "..."

        embedding = self.model.encode(text, convert_to_tensor=False)

        # Normalize the embedding for cosine similarity
        normalized_embedding = self._normalize_embedding(embedding)

        return normalized_embedding.tolist()

    async def generate_embeddings_batch(
        self,
        texts: list[str],
        use_cache: bool = True
    ) -> list[list[float]]:
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
                results[i] = []
                continue

            normalized_text = text.strip().lower()

            if use_cache and normalized_text in self._cache:
                results[i] = self._cache[normalized_text]
            else:
                texts_to_process.append((i, text, normalized_text))

        # Process remaining texts in batches
        if texts_to_process:
            await self._process_texts_batch(texts_to_process, results, use_cache)

        # Convert None results to empty lists
        final_results = [result if result is not None else [] for result in results]

        logger.debug(f"Generated {len(final_results)} embeddings")
        return final_results

    async def _process_texts_batch(
        self,
        texts_to_process: list[tuple],
        results: list[list[float] | None],
        use_cache: bool
    ) -> None:
        """
        Process texts in batches to generate embeddings.

        Args:
            texts_to_process: List of (index, text, normalized_text) tuples.
            results: Results list to update.
            use_cache: Whether to cache results.
        """
        # Process in batches to avoid memory issues
        for i in range(0, len(texts_to_process), self.batch_size):
            batch = texts_to_process[i:i + self.batch_size]
            batch_texts = [item[1] for item in batch]

            # Generate embeddings for batch
            batch_embeddings = await asyncio.get_event_loop().run_in_executor(
                None, self._generate_embeddings_batch_sync, batch_texts
            )

            # Store results
            for j, (original_index, _, normalized_text) in enumerate(batch):
                embedding = batch_embeddings[j]
                results[original_index] = embedding

                # Cache if requested
                if use_cache:
                    self._cache[normalized_text] = embedding

    def _generate_embeddings_batch_sync(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings for a batch of texts synchronously.

        Args:
            texts: List of texts to process.

        Returns:
            List[List[float]]: List of embedding vectors.
        """
        # Truncate long texts
        processed_texts = []
        for text in texts:
            if len(text) > 8000:
                text = text[:8000] + "..."
            processed_texts.append(text)

        # Generate embeddings
        embeddings = self.model.encode(processed_texts, convert_to_tensor=False)

        # Normalize embeddings
        normalized_embeddings = []
        for embedding in embeddings:
            normalized = self._normalize_embedding(embedding)
            normalized_embeddings.append(normalized.tolist())

        return normalized_embeddings

    def _normalize_embedding(self, embedding: np.ndarray) -> np.ndarray:
        """
        Normalize embedding vector for cosine similarity.

        Args:
            embedding: Raw embedding vector.

        Returns:
            np.ndarray: Normalized embedding vector.
        """
        norm = np.linalg.norm(embedding)
        if norm == 0:
            return embedding
        return embedding / norm

    def cosine_similarity(
        self,
        embedding1: list[float],
        embedding2: list[float]
    ) -> float:
        """
        Calculate cosine similarity between two embeddings.

        Args:
            embedding1: First embedding vector.
            embedding2: Second embedding vector.

        Returns:
            float: Cosine similarity score (0-1).
        """
        if len(embedding1) != len(embedding2):
            raise ValueError("Embeddings must have the same dimension")

        # Convert to numpy arrays
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)

        # Calculate cosine similarity
        # Since embeddings are normalized, dot product gives cosine similarity
        similarity = np.dot(vec1, vec2)

        # Clamp to valid range [0, 1] due to floating point precision
        return max(0.0, min(1.0, float(similarity)))

    async def generate_article_embedding(self, article_title: str, article_content: str) -> list[float]:
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
        logger.info("Embedding cache cleared")

    def get_model_info(self) -> dict[str, any]:
        """
        Get information about the embedding model.

        Returns:
            Dict: Model information.
        """
        return {
            "model_name": self.model_name,
            "embedding_dimension": 384,
            "batch_size": self.batch_size,
            "cache_size": self.get_cache_size(),
            "model_loaded": self._model is not None
        }


@lru_cache
def get_embeddings_service() -> EmbeddingsService:
    """
    Get singleton embeddings service instance.

    Returns:
        EmbeddingsService: Singleton service instance.
    """
    return EmbeddingsService()
