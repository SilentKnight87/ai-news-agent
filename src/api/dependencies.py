"""
FastAPI dependencies for dependency injection.

This module provides dependency functions for FastAPI routes
including database connections and service instances.
"""

import logging
from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from supabase import Client, create_client

from ..agents.news_agent import news_analyzer
from ..config import get_settings
from ..repositories.articles import ArticleRepository
from ..services.deduplication import DeduplicationService
from ..services.embeddings import get_embeddings_service

logger = logging.getLogger(__name__)


@lru_cache
def get_supabase_client() -> Client:
    """
    Get Supabase client instance.

    Returns:
        Client: Supabase client for database operations.
    """
    settings = get_settings()

    client = create_client(
        settings.supabase_url,
        settings.supabase_anon_key
    )

    logger.debug("Created Supabase client")
    return client


def get_article_repository(
    supabase: Annotated[Client, Depends(get_supabase_client)]
) -> ArticleRepository:
    """
    Get article repository instance.

    Args:
        supabase: Supabase client dependency.

    Returns:
        ArticleRepository: Article repository instance.
    """
    return ArticleRepository(supabase)


def get_deduplication_service(
    supabase: Annotated[Client, Depends(get_supabase_client)]
) -> DeduplicationService:
    """
    Get deduplication service instance.

    Args:
        supabase: Supabase client dependency.

    Returns:
        DeduplicationService: Deduplication service instance.
    """
    return DeduplicationService(supabase)


def get_news_analyzer():
    """
    Get news analyzer instance.

    Returns:
        NewsAnalyzer: News analyzer agent.
    """
    return news_analyzer


def get_embeddings_service():
    """
    Get embeddings service instance.

    Returns:
        EmbeddingsService: Embeddings service.
    """
    return get_embeddings_service()
