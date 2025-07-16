"""
Core data models for articles and news content.

This module defines the Pydantic models used throughout the application
for type safety and validation.
"""

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class ArticleSource(str, Enum):
    """Enumeration of supported news sources."""

    ARXIV = "arxiv"
    HACKERNEWS = "hackernews"
    RSS = "rss"


class Article(BaseModel):
    """
    Core article model with validation.

    Represents a news article from any source with AI-generated analysis
    and deduplication tracking.
    """

    # Core article data
    id: UUID | None = None
    source_id: str = Field(..., description="Unique identifier from the source")
    source: ArticleSource = Field(..., description="Source of the article")
    title: str = Field(..., min_length=1, max_length=500, description="Article title")
    content: str = Field(..., max_length=10000, description="Article content/summary")
    url: str = Field(..., description="URL to the original article")
    author: str | None = Field(None, description="Article author(s)")
    published_at: datetime = Field(..., description="When the article was published")
    fetched_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the article was fetched"
    )

    # AI-generated fields
    summary: str | None = Field(None, description="AI-generated summary")
    relevance_score: float | None = Field(
        None,
        ge=0,
        le=100,
        description="AI relevance score (0-100)"
    )
    categories: list[str] = Field(
        default_factory=list,
        description="AI-generated categories"
    )
    key_points: list[str] = Field(
        default_factory=list,
        description="AI-extracted key points"
    )

    # Vector embedding for similarity search (384-dimensional for all-MiniLM-L6-v2)
    embedding: list[float] | None = Field(
        None,
        description="Vector embedding for similarity search"
    )

    # Deduplication tracking
    is_duplicate: bool = Field(False, description="Whether this is a duplicate article")
    duplicate_of: UUID | None = Field(
        None,
        description="ID of the original article if this is a duplicate"
    )

    @field_validator('url')
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Validate that URL has proper protocol."""
        if not v.startswith(('http://', 'https://')):
            raise ValueError('URL must start with http:// or https://')
        return v

    @field_validator('embedding')
    @classmethod
    def validate_embedding_dimension(cls, v: list[float] | None) -> list[float] | None:
        """Validate embedding has correct dimensions."""
        if v is not None and len(v) != 384:
            raise ValueError('Embedding must have exactly 384 dimensions')
        return v

    @field_validator('categories')
    @classmethod
    def validate_categories(cls, v: list[str]) -> list[str]:
        """Validate categories list."""
        if len(v) > 5:
            raise ValueError('Maximum 5 categories allowed')
        return v

    @field_validator('key_points')
    @classmethod
    def validate_key_points(cls, v: list[str]) -> list[str]:
        """Validate key points list."""
        if len(v) > 5:
            raise ValueError('Maximum 5 key points allowed')
        return v


class ArticleCreate(BaseModel):
    """Model for creating new articles (without ID and computed fields)."""

    source_id: str
    source: ArticleSource
    title: str = Field(..., min_length=1, max_length=500)
    content: str = Field(..., max_length=10000)
    url: str
    author: str | None = None
    published_at: datetime


class ArticleUpdate(BaseModel):
    """Model for updating existing articles with AI analysis."""

    summary: str | None = None
    relevance_score: float | None = Field(None, ge=0, le=100)
    categories: list[str] | None = None
    key_points: list[str] | None = None
    embedding: list[float] | None = None
    is_duplicate: bool | None = None
    duplicate_of: UUID | None = None


class DailyDigest(BaseModel):
    """
    Daily digest model containing top articles.

    Represents a curated daily summary of the most relevant AI news.
    """

    id: UUID | None = None
    digest_date: datetime = Field(..., description="Date of the digest")
    summary_text: str = Field(
        ...,
        max_length=2000,
        description="Summary text for TTS generation"
    )
    total_articles_processed: int = Field(
        ...,
        ge=0,
        description="Number of articles processed for this digest"
    )
    audio_url: str | None = Field(None, description="URL to generated audio file")
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the digest was created"
    )

    # List of top articles included in the digest
    top_articles: list[Article] = Field(
        default_factory=list,
        description="Top articles included in this digest"
    )


class ArticleSimilarity(BaseModel):
    """Model for article similarity results."""

    article: Article
    similarity_score: float = Field(..., ge=0, le=1, description="Cosine similarity score")


class FetchResult(BaseModel):
    """Result of a fetch operation from a news source."""

    source: ArticleSource
    articles_fetched: int
    articles_new: int
    articles_duplicates: int
    errors: list[str] = Field(default_factory=list)
    fetch_duration_seconds: float
    success: bool
