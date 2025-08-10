"""
API schemas and PydanticAI agent output models.

This module defines the structured output schemas for PydanticAI agents
and API request/response models.
"""

from datetime import datetime

from pydantic import BaseModel, Field

from .articles import Article, ArticleSource, DailyDigest


class NewsAnalysis(BaseModel):
    """
    PydanticAI agent output schema for article analysis.

    This is the structured output that the news analysis agent returns
    when processing an article for relevance and key information.
    """

    summary: str = Field(
        ...,
        max_length=500,
        description="Concise summary of the article"
    )
    relevance_score: float = Field(
        ...,
        ge=0,
        le=100,
        description="Relevance score for AI/ML content (0-100)"
    )
    categories: list[str] = Field(
        ...,
        max_length=5,
        description="Relevant categories for this article"
    )
    key_points: list[str] = Field(
        ...,
        min_length=1,
        max_length=5,
        description="Key technical or business points"
    )


class DigestSummary(BaseModel):
    """
    PydanticAI agent output schema for daily digest generation.

    Used by the digest agent to create coherent daily summaries.
    """

    summary_text: str = Field(
        ...,
        max_length=2000,
        description="Coherent summary of top articles for the day"
    )
    key_themes: list[str] = Field(
        ...,
        max_length=5,
        description="Main themes emerging from today's news"
    )
    notable_developments: list[str] = Field(
        ...,
        max_length=3,
        description="Most significant developments to highlight"
    )


# API Request/Response Models

class ArticleListRequest(BaseModel):
    """Request parameters for listing articles."""

    limit: int = Field(10, ge=1, le=100, description="Number of articles to return")
    offset: int = Field(0, ge=0, description="Number of articles to skip")
    source: ArticleSource | None = Field(None, description="Filter by source")
    min_relevance_score: float | None = Field(None, ge=0, le=100)
    since: datetime | None = Field(None, description="Only articles after this date")


class ArticleListResponse(BaseModel):
    """Response for article listing."""

    articles: list[Article]
    total_count: int
    has_more: bool


class FetchTriggerRequest(BaseModel):
    """Request to manually trigger article fetching."""

    sources: list[ArticleSource] | None = Field(
        None,
        description="Specific sources to fetch, or all if None"
    )
    force: bool = Field(
        False,
        description="Force fetch even if recently fetched"
    )


class FetchTriggerResponse(BaseModel):
    """Response from fetch trigger."""

    message: str
    sources_triggered: list[ArticleSource]
    estimated_duration_minutes: int


class DigestRequest(BaseModel):
    """Request parameters for digest generation."""

    date: datetime | None = Field(None, description="Date for digest, today if None")
    regenerate: bool = Field(False, description="Regenerate if digest already exists")


class DigestResponse(BaseModel):
    """Response containing digest information."""

    digest: DailyDigest
    status: str = Field(..., description="Generation status")


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(..., description="Service status")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    version: str = Field("0.1.0", description="Application version")
    database_connected: bool
    last_fetch_time: datetime | None = None
    total_articles: int
    sources_status: dict = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    """Standard error response."""

    error: str = Field(..., description="Error message")
    error_code: str = Field(..., description="Error code for client handling")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: str | None = None


# Webhook payloads

class WebhookFetchPayload(BaseModel):
    """Payload for fetch webhook events."""

    event_type: str = Field("fetch_completed", description="Type of webhook event")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    sources: list[ArticleSource]
    total_articles_fetched: int
    total_new_articles: int
    total_duplicates: int
    duration_seconds: float
    errors: list[str] = Field(default_factory=list)


class WebhookDigestPayload(BaseModel):
    """Payload for digest generation webhook events."""

    event_type: str = Field("digest_generated", description="Type of webhook event")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    digest_date: datetime
    total_articles_processed: int
    audio_generated: bool


# New response models for core APIs

class PaginationMeta(BaseModel):
    """Standard pagination metadata."""
    
    page: int = Field(..., ge=1, description="Current page number")
    per_page: int = Field(..., ge=1, le=100, description="Items per page")
    total: int = Field(..., ge=0, description="Total number of items")
    total_pages: int = Field(..., ge=0, description="Total number of pages")
    has_next: bool = Field(..., description="Whether there is a next page")
    has_prev: bool = Field(..., description="Whether there is a previous page")


class SearchResponse(BaseModel):
    """Search endpoint response."""
    
    articles: list[Article] = Field(..., description="Search results")
    total: int = Field(..., ge=0, description="Total matching articles")
    query: str = Field(..., description="Search query used")
    took_ms: int = Field(..., ge=0, description="Query execution time in milliseconds")


class FilterResponse(BaseModel):
    """Filter endpoint response."""
    
    articles: list[Article] = Field(..., description="Filtered articles")
    filters_applied: dict = Field(..., description="Filters that were applied")
    total: int = Field(..., ge=0, description="Total matching articles")
    took_ms: int = Field(..., ge=0, description="Query execution time in milliseconds")


class PaginatedArticleResponse(BaseModel):
    """Enhanced article list with pagination."""
    
    articles: list[Article] = Field(..., description="Page of articles")
    pagination: PaginationMeta = Field(..., description="Pagination metadata")
    meta: dict = Field(default_factory=dict, description="Additional metadata")


class DigestSummaryItem(BaseModel):
    """Digest summary for list view."""
    
    id: str = Field(..., description="Digest ID")
    date: str = Field(..., description="Digest date")
    title: str = Field(..., description="Digest title")
    summary: str = Field(..., max_length=2000, description="Digest summary")
    key_developments: list[str] = Field(..., description="Key developments")
    article_count: int = Field(..., ge=0, description="Number of articles")
    audio_url: str | None = Field(None, description="Audio file URL")
    audio_duration: int | None = Field(None, description="Audio duration in seconds")
    created_at: datetime = Field(..., description="Creation timestamp")


class DigestListResponse(BaseModel):
    """Digest list endpoint response."""
    
    digests: list[DigestSummaryItem] = Field(..., description="List of digests")
    pagination: PaginationMeta = Field(..., description="Pagination metadata")


class ArticleSummary(BaseModel):
    """Simplified article for digest view."""
    
    id: str = Field(..., description="Article ID")
    title: str = Field(..., description="Article title")
    summary: str | None = Field(None, description="Article summary")
    source: str = Field(..., description="Article source")
    url: str = Field(..., description="Article URL")
    relevance_score: float | None = Field(None, ge=0, le=100, description="Relevance score")


class DigestDetailResponse(BaseModel):
    """Single digest endpoint response."""
    
    id: str = Field(..., description="Digest ID")
    date: str = Field(..., description="Digest date")
    title: str = Field(..., description="Digest title")
    summary: str = Field(..., max_length=2000, description="Full digest summary")
    key_developments: list[str] = Field(..., description="Key developments")
    articles: list[ArticleSummary] = Field(..., description="Articles in this digest")
    audio_url: str | None = Field(None, description="Audio file URL")
    audio_duration: int | None = Field(None, description="Audio duration in seconds")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class SourceMetadata(BaseModel):
    """Source metadata item."""
    
    name: str = Field(..., description="Source identifier")
    display_name: str = Field(..., description="Display name")
    description: str = Field(..., description="Source description")
    article_count: int = Field(..., ge=0, description="Number of articles")
    last_fetch: datetime | None = Field(None, description="Last fetch time")
    last_published: datetime | None = Field(None, description="Last article published time")
    avg_relevance_score: float = Field(..., ge=0, le=100, description="Average relevance score")
    status: str = Field(..., description="Source status")
    icon_url: str = Field(..., description="Icon URL")
    categories: list[str] = Field(default_factory=list, description="Common categories")


class SourcesMetadataResponse(BaseModel):
    """Sources metadata endpoint response."""
    
    sources: list[SourceMetadata] = Field(..., description="List of sources")
    total_sources: int = Field(..., ge=0, description="Total number of sources")
    active_sources: int = Field(..., ge=0, description="Number of active sources")
    total_articles: int = Field(..., ge=0, description="Total articles across all sources")
    digest_url: str | None = None
    audio_url: str | None = None
