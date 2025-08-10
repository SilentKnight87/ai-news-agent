"""
FastAPI routes for the AI news aggregator API.

This module defines all the API endpoints for the news aggregator
including article management, fetching, and digest operations.
"""

import logging
import time
from datetime import datetime, timedelta, date
from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query

from ..agents.news_agent import NewsAnalyzer
from ..fetchers.factory import fetcher_factory
from ..models.articles import Article, ArticleSource
from ..models.schemas import (
    ArticleListResponse,
    DigestResponse,
    FetchTriggerRequest,
    FetchTriggerResponse,
    HealthResponse,
    SearchResponse,
    FilterResponse,
    PaginatedArticleResponse,
    DigestListResponse,
    DigestDetailResponse,
    SourcesMetadataResponse,
    PaginationMeta,
    DigestSummaryItem,
    ArticleSummary,
    SourceMetadata,
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


@router.get("/articles/search", response_model=SearchResponse)
async def search_articles(
    q: str = Query(..., description="Search query", min_length=1),
    source: Optional[ArticleSource] = Query(None, description="Filter by source"),
    limit: int = Query(20, ge=1, le=100, description="Results per page"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    article_repo: ArticleRepository = Depends(get_article_repository)
) -> SearchResponse:
    """
    Full-text search across article titles and content.
    
    Searches article titles and content using PostgreSQL full-text search
    capabilities when available, with fallback to pattern matching.
    
    Args:
        q: Search query text (required, min length 1)
        source: Optional source filter
        limit: Number of results (1-100, default 20)
        offset: Pagination offset (default 0)
        article_repo: Article repository dependency
        
    Returns:
        SearchResponse: Search results with timing information
    """
    try:
        start_time = time.time()
        
        # Perform search
        articles, total = await article_repo.search_articles(
            query=q,
            source=source,
            limit=limit,
            offset=offset
        )
        
        took_ms = int((time.time() - start_time) * 1000)
        
        return SearchResponse(
            articles=articles,
            total=total,
            query=q,
            took_ms=took_ms
        )
        
    except Exception as e:
        logger.error(f"Search failed for query '{q}': {e}")
        raise HTTPException(
            status_code=500,
            detail="Search operation failed"
        )


@router.get("/articles/filter", response_model=FilterResponse)
async def filter_articles(
    start_date: Optional[date] = Query(None, description="Filter articles after this date"),
    end_date: Optional[date] = Query(None, description="Filter articles before this date"),
    relevance_min: Optional[int] = Query(None, ge=0, le=100, description="Minimum relevance score"),
    relevance_max: Optional[int] = Query(None, ge=0, le=100, description="Maximum relevance score"),
    sources: Optional[str] = Query(None, description="Comma-separated source list"),
    categories: Optional[str] = Query(None, description="Comma-separated category list"),
    limit: int = Query(20, ge=1, le=100, description="Results per page"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    article_repo: ArticleRepository = Depends(get_article_repository)
) -> FilterResponse:
    """
    Advanced filtering with multiple criteria.
    
    Filter articles by date range, relevance score, sources, and categories.
    All filters are optional and can be combined.
    
    Args:
        start_date: Filter articles published after this date
        end_date: Filter articles published before this date
        relevance_min: Minimum relevance score (0-100)
        relevance_max: Maximum relevance score (0-100)
        sources: Comma-separated list of sources
        categories: Comma-separated list of categories
        limit: Results per page
        offset: Pagination offset
        article_repo: Article repository dependency
        
    Returns:
        FilterResponse: Filtered articles with applied filters info
    """
    try:
        start_time = time.time()
        
        # Parse comma-separated lists
        source_list = None
        if sources:
            source_list = [ArticleSource(s.strip()) for s in sources.split(",")]
            
        category_list = None
        if categories:
            category_list = [c.strip() for c in categories.split(",")]
        
        # Convert dates to datetime if provided
        start_datetime = datetime.combine(start_date, datetime.min.time()) if start_date else None
        end_datetime = datetime.combine(end_date, datetime.max.time()) if end_date else None
        
        # Apply filters
        articles, total = await article_repo.filter_articles(
            start_date=start_datetime,
            end_date=end_datetime,
            relevance_min=relevance_min,
            relevance_max=relevance_max,
            sources=source_list,
            categories=category_list,
            limit=limit,
            offset=offset
        )
        
        # Build filters_applied dict
        filters_applied = {}
        if start_date:
            filters_applied["start_date"] = str(start_date)
        if end_date:
            filters_applied["end_date"] = str(end_date)
        if relevance_min is not None:
            filters_applied["relevance_min"] = relevance_min
        if relevance_max is not None:
            filters_applied["relevance_max"] = relevance_max
        if sources:
            filters_applied["sources"] = source_list
        if categories:
            filters_applied["categories"] = category_list
            
        took_ms = int((time.time() - start_time) * 1000)
        
        return FilterResponse(
            articles=articles,
            filters_applied=filters_applied,
            total=total,
            took_ms=took_ms
        )
        
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Filter articles failed: {e}")
        raise HTTPException(
            status_code=500,
            detail="Filter operation failed"
        )


@router.get("/articles", response_model=PaginatedArticleResponse)
async def get_articles_paginated(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    sort_by: str = Query("published_at", description="Field to sort by"),
    order: str = Query("desc", pattern="^(asc|desc)$", description="Sort order"),
    source: Optional[ArticleSource] = Query(None, description="Filter by source"),
    article_repo: ArticleRepository = Depends(get_article_repository)
) -> PaginatedArticleResponse:
    """
    Get paginated articles with enhanced pagination metadata.
    
    Replaces the basic article listing with proper pagination support
    including page numbers, total pages, and navigation flags.
    
    Args:
        page: Page number (starts at 1)
        per_page: Items per page (1-100)
        sort_by: Field to sort by (published_at, relevance_score, title)
        order: Sort order (asc or desc)
        source: Optional source filter
        article_repo: Article repository dependency
        
    Returns:
        PaginatedArticleResponse: Articles with full pagination metadata
    """
    try:
        # Validate sort_by field
        valid_sort_fields = ["published_at", "relevance_score", "title", "fetched_at"]
        if sort_by not in valid_sort_fields:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid sort_by field. Must be one of: {', '.join(valid_sort_fields)}"
            )
        
        # Get paginated results
        articles, total = await article_repo.get_articles_paginated(
            page=page,
            per_page=per_page,
            sort_by=sort_by,
            order=order,
            source=source
        )
        
        # Calculate pagination metadata
        total_pages = (total + per_page - 1) // per_page if total > 0 else 0
        has_next = page < total_pages
        has_prev = page > 1
        
        pagination = PaginationMeta(
            page=page,
            per_page=per_page,
            total=total,
            total_pages=total_pages,
            has_next=has_next,
            has_prev=has_prev
        )
        
        meta = {
            "sort_by": sort_by,
            "order": order,
            "cache_hit": False
        }
        
        return PaginatedArticleResponse(
            articles=articles,
            pagination=pagination,
            meta=meta
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get paginated articles failed: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve articles"
        )


# Legacy articles list endpoint - deprecated, use paginated version above
@router.get("/articles/legacy", response_model=ArticleListResponse)
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


@router.get("/scheduler/status")
async def get_scheduler_status():
    """
    Get current scheduler status and task information.
    
    Returns:
        Dict: Scheduler status with task details.
    """
    from ..services.scheduler import get_scheduler
    
    scheduler = get_scheduler()
    return scheduler.get_status()


@router.post("/scheduler/task/{task_name}/run")
async def run_scheduler_task(task_name: str):
    """
    Manually trigger a scheduled task to run immediately.
    
    Args:
        task_name: Name of the task to run.
        
    Returns:
        Dict: Task execution result.
    """
    from ..services.scheduler import get_scheduler
    
    scheduler = get_scheduler()
    success = await scheduler.run_task_now(task_name)
    
    if not success:
        raise HTTPException(status_code=404, detail=f"Task '{task_name}' not found or execution failed")
    
    return {
        "message": f"Task '{task_name}' executed successfully",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/monitoring/performance")
async def get_performance_metrics(
    article_repo: Annotated[ArticleRepository, Depends(get_article_repository)]
):
    """
    Get comprehensive performance and monitoring metrics.
    
    Returns:
        Dict: Performance metrics for monitoring.
    """
    try:
        # Get article statistics
        stats = await article_repo.get_article_stats()
        
        # Get scheduler status  
        from ..services.scheduler import get_scheduler
        scheduler = get_scheduler()
        scheduler_status = scheduler.get_status()
        
        # Get fetcher health status
        fetcher_health = fetcher_factory.get_health_status()
        
        # Calculate performance metrics
        total_articles = stats.get("total_articles", 0)
        recent_24h = stats.get("recent_24h", 0)
        duplicates = stats.get("duplicates", 0)
        
        # Calculate rates
        duplicate_rate = (duplicates / total_articles * 100) if total_articles > 0 else 0
        daily_collection_rate = recent_24h  # Articles per day
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "database": {
                "connection_healthy": "error" not in stats,
                "total_articles": total_articles,
                "recent_24h_articles": recent_24h,
                "duplicate_rate_percent": round(duplicate_rate, 2),
                "daily_collection_rate": daily_collection_rate
            },
            "scheduler": {
                "is_running": scheduler_status.get("is_running", False),
                "total_tasks": scheduler_status.get("total_tasks", 0),
                "next_task_run": scheduler_status.get("next_task_run"),
                "task_health": [
                    {
                        "name": task["name"],
                        "success_rate": task["success_rate"],
                        "error_count": task["error_count"],
                        "last_run": task["last_run"]
                    }
                    for task in scheduler_status.get("tasks", [])
                ]
            },
            "fetchers": {
                "total_sources": len(fetcher_health.get("supported_sources", [])),
                "active_sources": len(fetcher_health.get("active_instances", [])),
                "sources_status": fetcher_health.get("fetcher_status", {}),
                "circuit_breakers_open": [
                    source for source, status in fetcher_health.get("fetcher_status", {}).items()
                    if status.get("circuit_breaker_open", False)
                ]
            },
            "performance": {
                "collection_efficiency": round((total_articles - duplicates) / total_articles * 100, 2) if total_articles > 0 else 100,
                "avg_articles_per_source": round(total_articles / len(fetcher_health.get("supported_sources", [1])), 2),
                "data_freshness_hours": 24 if recent_24h > 0 else None
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get performance metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve performance metrics")


# ============================================================================
# New Core API Endpoints for MVP - Digests
# ============================================================================


@router.get("/digests", response_model=DigestListResponse)
async def get_digests(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=50, description="Digests per page"),
    article_repo: ArticleRepository = Depends(get_article_repository)
) -> DigestListResponse:
    """
    Get paginated list of daily digests.
    
    Returns all available digests with summary information,
    ordered by date descending (newest first).
    
    Args:
        page: Page number (starts at 1)
        per_page: Items per page (1-50)
        article_repo: Article repository dependency
        
    Returns:
        DigestListResponse: List of digests with pagination
    """
    try:
        # Get digests from repository
        digest_dicts, total = await article_repo.get_digests(
            page=page,
            per_page=per_page
        )
        
        # Convert to response models
        digests = []
        for digest_data in digest_dicts:
            digest_item = DigestSummaryItem(
                id=digest_data["id"],
                date=digest_data["date"],
                title=digest_data["title"],
                summary=digest_data["summary"],
                key_developments=digest_data["key_developments"],
                article_count=digest_data["article_count"],
                audio_url=digest_data.get("audio_url"),
                audio_duration=digest_data.get("audio_duration"),
                created_at=datetime.fromisoformat(digest_data["created_at"].replace("Z", "+00:00"))
            )
            digests.append(digest_item)
        
        # Calculate pagination
        total_pages = (total + per_page - 1) // per_page if total > 0 else 0
        
        pagination = PaginationMeta(
            page=page,
            per_page=per_page,
            total=total,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1
        )
        
        return DigestListResponse(
            digests=digests,
            pagination=pagination
        )
        
    except Exception as e:
        logger.error(f"Get digests failed: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve digests"
        )


@router.get("/digests/{digest_id}", response_model=DigestDetailResponse)
async def get_digest_by_id(
    digest_id: UUID,
    article_repo: ArticleRepository = Depends(get_article_repository)
) -> DigestDetailResponse:
    """
    Get a single digest with all its articles.
    
    Returns complete digest information including all articles
    that were included in the digest.
    
    Args:
        digest_id: Digest UUID
        article_repo: Article repository dependency
        
    Returns:
        DigestDetailResponse: Complete digest with articles
        
    Raises:
        HTTPException: 404 if digest not found
    """
    try:
        # Get digest from repository
        digest_data = await article_repo.get_digest_by_id(digest_id)
        
        if not digest_data:
            raise HTTPException(status_code=404, detail="Digest not found")
        
        # Convert articles to ArticleSummary
        articles = []
        for article_data in digest_data.get("articles", []):
            article_summary = ArticleSummary(
                id=article_data["id"],
                title=article_data["title"],
                summary=article_data.get("summary"),
                source=article_data["source"],
                url=article_data["url"],
                relevance_score=article_data.get("relevance_score")
            )
            articles.append(article_summary)
        
        return DigestDetailResponse(
            id=digest_data["id"],
            date=digest_data["date"],
            title=digest_data["title"],
            summary=digest_data["summary"],
            key_developments=digest_data["key_developments"],
            articles=articles,
            audio_url=digest_data.get("audio_url"),
            audio_duration=digest_data.get("audio_duration"),
            created_at=datetime.fromisoformat(digest_data["created_at"].replace("Z", "+00:00")),
            updated_at=datetime.fromisoformat(digest_data["updated_at"].replace("Z", "+00:00"))
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get digest by ID failed: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve digest"
        )


@router.get("/sources", response_model=SourcesMetadataResponse)
async def get_sources_metadata(
    article_repo: ArticleRepository = Depends(get_article_repository)
) -> SourcesMetadataResponse:
    """
    Get metadata about all available sources.
    
    Returns information about each source including article counts,
    last fetch times, and status information.
    
    Args:
        article_repo: Article repository dependency
        
    Returns:
        SourcesMetadataResponse: Source metadata and statistics
    """
    try:
        # Get sources metadata from repository
        sources_data = await article_repo.get_sources_metadata()
        
        # Get overall stats
        stats = await article_repo.get_article_stats()
        total_articles = stats.get("total_articles", 0)
        
        # Get fetcher health for last fetch times
        fetcher_health = fetcher_factory.get_health_status()
        fetcher_status = fetcher_health.get("fetcher_status", {})
        
        # Convert to response models
        sources = []
        for source_data in sources_data:
            # Get last fetch time from fetcher status
            source_name = source_data["name"]
            fetcher_info = fetcher_status.get(source_name, {})
            last_fetch = fetcher_info.get("last_request_time")
            
            if last_fetch:
                last_fetch = datetime.fromisoformat(last_fetch.replace("Z", "+00:00"))
            
            # Parse last published if it's a string
            last_published = source_data.get("last_published")
            if last_published and isinstance(last_published, str):
                last_published = datetime.fromisoformat(last_published.replace("Z", "+00:00"))
            
            source_meta = SourceMetadata(
                name=source_data["name"],
                display_name=source_data["display_name"],
                description=source_data["description"],
                article_count=source_data["article_count"],
                last_fetch=last_fetch,
                last_published=last_published,
                avg_relevance_score=source_data["avg_relevance_score"],
                status=source_data["status"],
                icon_url=source_data["icon_url"],
                categories=[]
            )
            sources.append(source_meta)
        
        # Count active sources
        active_sources = sum(1 for s in sources if s.status == "active")
        
        return SourcesMetadataResponse(
            sources=sources,
            total_sources=len(sources),
            active_sources=active_sources,
            total_articles=total_articles
        )
        
    except Exception as e:
        logger.error(f"Get sources metadata failed: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve sources metadata"
        )


# Note: Exception handlers are configured in main.py
