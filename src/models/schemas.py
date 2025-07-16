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
        max_items=5,
        description="Relevant categories for this article"
    )
    key_points: list[str] = Field(
        ...,
        min_items=1,
        max_items=5,
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
        max_items=5,
        description="Main themes emerging from today's news"
    )
    notable_developments: list[str] = Field(
        ...,
        max_items=3,
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
    digest_url: str | None = None
    audio_url: str | None = None
