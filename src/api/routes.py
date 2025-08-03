"""
FastAPI routes for the AI news aggregator API.

This module defines all the API endpoints for the news aggregator
including article management, fetching, and digest operations.
"""

import logging
from datetime import datetime, timedelta
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from ..agents.news_agent import NewsAnalyzer
from ..fetchers.factory import fetcher_factory
from ..models.articles import Article, ArticleSource
from ..models.schemas import (
    ArticleListResponse,
    DigestResponse,
    FetchTriggerRequest,
    FetchTriggerResponse,
    HealthResponse,
)
from ..repositories.articles import ArticleRepository
from ..services.deduplication import DeduplicationService
from .dependencies import (
    get_article_repository,
    get_deduplication_service,
    get_news_analyzer,
)

logger = logging.getLogger(__name__)

# Create router
router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check(
    article_repo: Annotated[ArticleRepository, Depends(get_article_repository)]
) -> HealthResponse:
    """
    Health check endpoint.

    Returns:
        HealthResponse: Current service health status.
    """
    try:
        # Test database connection
        stats = await article_repo.get_article_stats()
        database_connected = "error" not in stats

        # Get fetcher status
        sources_status = fetcher_factory.get_health_status()

        # Get last fetch time (approximate from most recent article)
        recent_articles = await article_repo.get_articles(limit=1)
        last_fetch_time = recent_articles[0].fetched_at if recent_articles else None

        return HealthResponse(
            status="healthy" if database_connected else "unhealthy",
            database_connected=database_connected,
            last_fetch_time=last_fetch_time,
            total_articles=stats.get("total_articles", 0),
            sources_status=sources_status
        )

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthResponse(
            status="unhealthy",
            database_connected=False,
            total_articles=0,
            sources_status={}
        )


@router.get("/articles", response_model=ArticleListResponse)
async def list_articles(
    article_repo: Annotated[ArticleRepository, Depends(get_article_repository)],
    limit: int = 10,
    offset: int = 0,
    source: ArticleSource | None = None,
    min_relevance_score: float | None = None,
    since_hours: int | None = None
) -> ArticleListResponse:
    """
    List articles with filtering and pagination.

    Args:
        limit: Number of articles to return (max 100).
        offset: Number of articles to skip.
        source: Filter by specific source.
        min_relevance_score: Minimum relevance score (0-100).
        since_hours: Only include articles from last N hours.
        article_repo: Article repository dependency.

    Returns:
        ArticleListResponse: Paginated list of articles.
    """
    try:
        # Validate parameters
        if limit > 100:
            limit = 100
        if limit < 1:
            limit = 1

        # Calculate since date if provided
        since = None
        if since_hours is not None:
            since = datetime.utcnow() - timedelta(hours=since_hours)

        # Get articles
        articles = await article_repo.get_articles(
            limit=limit + 1,  # Get one extra to check if there are more
            offset=offset,
            source=source,
            min_relevance_score=min_relevance_score,
            since=since,
            include_duplicates=False
        )

        # Check if there are more articles
        has_more = len(articles) > limit
        if has_more:
            articles = articles[:limit]

        # Get total count (approximate for performance)
        total_count = offset + len(articles)
        if has_more:
            total_count += 1  # At least one more

        return ArticleListResponse(
            articles=articles,
            total_count=total_count,
            has_more=has_more
        )

    except Exception as e:
        logger.error(f"Failed to list articles: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve articles")


@router.get("/articles/{article_id}", response_model=Article)
async def get_article(
    article_id: UUID,
    article_repo: Annotated[ArticleRepository, Depends(get_article_repository)]
) -> Article:
    """
    Get a specific article by ID.

    Args:
        article_id: Article ID to retrieve.
        article_repo: Article repository dependency.

    Returns:
        Article: The requested article.

    Raises:
        HTTPException: If article not found.
    """
    try:
        article = await article_repo.get_article_by_id(article_id)

        if not article:
            raise HTTPException(status_code=404, detail="Article not found")

        return article

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get article {article_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve article")


@router.post("/webhook/fetch", response_model=FetchTriggerResponse)
async def trigger_fetch(
    request: FetchTriggerRequest,
    background_tasks: BackgroundTasks,
    article_repo: Annotated[ArticleRepository, Depends(get_article_repository)],
    deduplication_service: Annotated[DeduplicationService, Depends(get_deduplication_service)],
    news_analyzer: Annotated[NewsAnalyzer, Depends(get_news_analyzer)]
) -> FetchTriggerResponse:
    """
    Manually trigger article fetching from sources.

    Args:
        request: Fetch trigger request.
        background_tasks: FastAPI background tasks.
        article_repo: Article repository dependency.
        deduplication_service: Deduplication service dependency.
        news_analyzer: News analyzer dependency.

    Returns:
        FetchTriggerResponse: Fetch trigger response.
    """
    try:
        # Determine which sources to fetch
        sources_to_fetch = request.sources or list(ArticleSource)

        # Add background task for fetching
        background_tasks.add_task(
            fetch_articles_background,
            sources_to_fetch,
            article_repo,
            deduplication_service,
            news_analyzer
        )

        return FetchTriggerResponse(
            message="Fetch triggered successfully",
            sources_triggered=sources_to_fetch,
            estimated_duration_minutes=len(sources_to_fetch) * 2  # Rough estimate
        )

    except Exception as e:
        logger.error(f"Failed to trigger fetch: {e}")
        raise HTTPException(status_code=500, detail="Failed to trigger fetch")


@router.get("/digest/latest", response_model=DigestResponse)
async def get_latest_digest(
    article_repo: Annotated[ArticleRepository, Depends(get_article_repository)]
) -> DigestResponse:
    """
    Get the latest daily digest.

    Args:
        article_repo: Article repository dependency.

    Returns:
        DigestResponse: Latest digest information.
    """
    try:
        # Get top articles from last 24 hours
        top_articles = await article_repo.get_top_articles_for_digest(
            since_hours=24,
            min_relevance_score=50.0,
            limit=10
        )

        if not top_articles:
            raise HTTPException(status_code=404, detail="No articles found for digest")

        # Create digest object (simplified for now)
        from ..models.articles import DailyDigest
        digest = DailyDigest(
            digest_date=datetime.utcnow(),
            summary_text=f"Top {len(top_articles)} AI/ML stories from the last 24 hours",
            total_articles_processed=len(top_articles),
            top_articles=top_articles
        )

        return DigestResponse(
            digest=digest,
            status="generated"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get latest digest: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve digest")


@router.get("/stats")
async def get_stats(
    article_repo: Annotated[ArticleRepository, Depends(get_article_repository)],
    deduplication_service: Annotated[DeduplicationService, Depends(get_deduplication_service)]
) -> dict:
    """
    Get aggregated statistics about the news aggregator.

    Args:
        article_repo: Article repository dependency.
        deduplication_service: Deduplication service dependency.

    Returns:
        dict: Statistics information.
    """
    try:
        # Get article stats
        article_stats = await article_repo.get_article_stats()

        # Get deduplication stats
        dedup_stats = deduplication_service.get_deduplication_stats()

        # Get fetcher health
        fetcher_health = fetcher_factory.get_health_status()

        return {
            "articles": article_stats,
            "deduplication": dedup_stats,
            "fetchers": fetcher_health,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve statistics")


@router.post("/articles/{article_id}/analyze")
async def analyze_article(
    article_id: UUID,
    article_repo: Annotated[ArticleRepository, Depends(get_article_repository)],
    news_analyzer: Annotated[NewsAnalyzer, Depends(get_news_analyzer)]
) -> Article:
    """
    Re-analyze an article with the AI agent.

    Args:
        article_id: Article ID to analyze.
        article_repo: Article repository dependency.
        news_analyzer: News analyzer dependency.

    Returns:
        Article: Updated article with analysis.
    """
    try:
        # Get the article
        article = await article_repo.get_article_by_id(article_id)
        if not article:
            raise HTTPException(status_code=404, detail="Article not found")

        # Analyze the article
        analysis = await news_analyzer.analyze_article(article)

        # Update the article with analysis
        updated_article = await article_repo.update_article_analysis(
            article_id=article_id,
            summary=analysis.summary,
            relevance_score=analysis.relevance_score,
            categories=analysis.categories,
            key_points=analysis.key_points
        )

        if not updated_article:
            raise HTTPException(status_code=500, detail="Failed to update article")

        return updated_article

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to analyze article {article_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to analyze article")


async def fetch_articles_background(
    sources: list[ArticleSource],
    article_repo: ArticleRepository,
    deduplication_service: DeduplicationService,
    news_analyzer: NewsAnalyzer
) -> None:
    """
    Background task for fetching and processing articles.

    Args:
        sources: List of sources to fetch from.
        article_repo: Article repository.
        deduplication_service: Deduplication service.
        news_analyzer: News analyzer.
    """
    try:
        logger.info(f"Starting background fetch for sources: {sources}")

        all_articles = []

        # Fetch from each source
        for source in sources:
            try:
                fetcher = fetcher_factory.get_fetcher(source)
                source_articles = await fetcher.fetch(max_articles=50)

                logger.info(f"Fetched {len(source_articles)} articles from {source}")
                all_articles.extend(source_articles)

            except Exception as e:
                logger.error(f"Failed to fetch from {source}: {e}")
                continue

        if not all_articles:
            logger.warning("No articles fetched from any source")
            return

        # Analyze articles for relevance
        analyzed_articles = await news_analyzer.analyze_and_update_articles(
            all_articles, min_relevance_score=50.0
        )

        if not analyzed_articles:
            logger.info("No relevant articles found after analysis")
            return

        # Process for duplicates
        unique_articles, duplicates = await deduplication_service.process_articles_for_duplicates(
            analyzed_articles
        )

        # Store unique articles in database
        if unique_articles:
            created_articles = await article_repo.batch_create_articles(unique_articles)
            logger.info(f"Stored {len(created_articles)} new articles")

        # Store duplicates (marked as such)
        if duplicates:
            created_duplicates = await article_repo.batch_create_articles(duplicates)
            logger.info(f"Stored {len(created_duplicates)} duplicate articles")

        logger.info("Background fetch completed successfully")

    except Exception as e:
        logger.error(f"Background fetch failed: {e}")


# Note: Exception handlers are configured in main.py
