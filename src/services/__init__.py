"""Core services for news processing."""
import os
import logging

logger = logging.getLogger(__name__)

def get_embeddings_service():
    """
    Factory that returns the appropriate embeddings service based on environment.

    Behavior:
    - EMBEDDINGS_PROVIDER=openai -> returns OpenAIEmbeddingsService (uses OPENAI_API_KEY)
    - EMBEDDINGS_PROVIDER=local (default) -> returns local Sentence-Transformers service

    Returns:
        An embeddings service instance exposing:
          - generate_embedding(text, use_cache=True)
          - generate_embeddings_batch(texts, use_cache=True)
          - cosine_similarity(a, b)
          - get_model_info()
    """
    provider = os.getenv("EMBEDDINGS_PROVIDER", "local").strip().lower()

    if provider == "openai":
        from src.services.embeddings_openai import OpenAIEmbeddingsService
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.error("EMBEDDINGS_PROVIDER=openai but OPENAI_API_KEY is not set")
            raise RuntimeError("OPENAI_API_KEY is required when EMBEDDINGS_PROVIDER=openai")
        logger.info("Using OpenAIEmbeddingsService (production)")
        return OpenAIEmbeddingsService(api_key=api_key)

    # Fallback to local model (development)
    logger.info("Using local Sentence-Transformers EmbeddingsService (development)")
    from src.services.embeddings import get_embeddings_service as _local_factory
    return _local_factory()
