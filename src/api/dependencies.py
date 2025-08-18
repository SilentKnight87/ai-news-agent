"""
FastAPI dependencies for dependency injection.

This module provides dependency functions for FastAPI routes
including database connections and service instances.
"""

import logging
import os
from functools import lru_cache
from typing import Annotated

import httpx
from fastapi import Depends
from supabase import Client, create_client
from supabase.lib.client_options import ClientOptions

from ..agents.news_agent import get_news_analyzer as get_analyzer_instance
from ..config import get_settings
from ..repositories.articles import ArticleRepository
from ..services.deduplication import DeduplicationService
from ..services.embeddings import get_embeddings_service

logger = logging.getLogger(__name__)


@lru_cache
def get_supabase_client() -> Client:
    """
    Get Supabase client with connection pooling.

    Returns:
        Client: Supabase client for database operations.
    """
    settings = get_settings()

    # Prefer service role key for write operations (GitHub Actions)
    service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    key_to_use = service_key if service_key else settings.supabase_anon_key
    
    if not key_to_use:
        raise ValueError("Either SUPABASE_SERVICE_ROLE_KEY environment variable or supabase_anon_key setting must be provided")

    # Configure connection pool
    options = ClientOptions(
        schema="public",
        headers={"x-my-custom-header": "ai-news-aggregator"},
        auto_refresh_token=True,
        persist_session=True,
        storage={},
        flow_type="implicit",
        realtime={
            "params": {
                "eventsPerSecond": 10
            }
        }
    )

    # Create client with connection pooling

    client = create_client(
        settings.supabase_url,
        key_to_use,  # Use service key if available
        options=options
    )

    logger.debug("Created Supabase client with connection pooling")
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
    return get_analyzer_instance()


