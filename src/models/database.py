"""
SQLAlchemy database models for the AI news aggregator.

These models map to the database schema defined in migrations/001_initial_schema.sql
and are used for direct database operations through the repository layer.
"""

from uuid import uuid4

from sqlalchemy import (
    ARRAY,
    TIMESTAMP,
    Boolean,
    Column,
    Date,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy import (
    Enum as SQLEnum,
)
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .articles import ArticleSource

Base = declarative_base()


class ArticleDB(Base):
    """SQLAlchemy model for articles table."""

    __tablename__ = "articles"

    # Primary key and identifiers
    id = Column(PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid4)
    source_id = Column(String, nullable=False)
    source = Column(SQLEnum(ArticleSource), nullable=False)

    # Content fields
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    url = Column(String, nullable=False)
    author = Column(String, nullable=True)

    # Timestamps
    published_at = Column(TIMESTAMP(timezone=True), nullable=False)
    fetched_at = Column(TIMESTAMP(timezone=True), nullable=False, default=func.now())

    # AI-generated fields
    summary = Column(Text, nullable=True)
    relevance_score = Column(Float, nullable=True)
    categories = Column(ARRAY(String), default=[], nullable=False)
    key_points = Column(ARRAY(String), default=[], nullable=False)

    # Vector embedding (pgvector extension)
    # Note: This would need pgvector.Vector type in production
    # For now, we'll handle as JSON and convert in the repository layer
    embedding = Column(Text, nullable=True)  # JSON-encoded list of floats

    # Deduplication
    is_duplicate = Column(Boolean, nullable=False, default=False)
    duplicate_of = Column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("articles.id"),
        nullable=True
    )

    # Relationships
    duplicates = relationship("ArticleDB", remote_side=[id])
    digest_associations = relationship("DigestArticleDB", back_populates="article")

    # Constraints
    __table_args__ = (
        UniqueConstraint("source", "source_id", name="uq_source_article"),
    )


class DailyDigestDB(Base):
    """SQLAlchemy model for daily_digests table."""

    __tablename__ = "daily_digests"

    id = Column(PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid4)
    digest_date = Column(Date, nullable=False, unique=True)
    summary_text = Column(Text, nullable=False)
    total_articles_processed = Column(Integer, nullable=False)
    audio_url = Column(String, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, default=func.now())

    # Relationships
    article_associations = relationship("DigestArticleDB", back_populates="digest")


class DigestArticleDB(Base):
    """SQLAlchemy model for digest_articles junction table."""

    __tablename__ = "digest_articles"

    digest_id = Column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("daily_digests.id", ondelete="CASCADE"),
        primary_key=True
    )
    article_id = Column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("articles.id", ondelete="CASCADE"),
        primary_key=True
    )

    # Relationships
    digest = relationship("DailyDigestDB", back_populates="article_associations")
    article = relationship("ArticleDB", back_populates="digest_associations")


# Utility functions for model conversion

def article_db_to_pydantic(article_db: ArticleDB) -> "Article":
    """
    Convert SQLAlchemy ArticleDB to Pydantic Article model.

    Args:
        article_db: SQLAlchemy article instance.

    Returns:
        Article: Pydantic article model.
    """
    import json

    from .articles import Article

    # Convert embedding from JSON string back to list
    embedding = None
    if article_db.embedding:
        try:
            embedding = json.loads(article_db.embedding)
        except (json.JSONDecodeError, TypeError):
            embedding = None

    return Article(
        id=article_db.id,
        source_id=article_db.source_id,
        source=article_db.source,
        title=article_db.title,
        content=article_db.content,
        url=article_db.url,
        author=article_db.author,
        published_at=article_db.published_at,
        fetched_at=article_db.fetched_at,
        summary=article_db.summary,
        relevance_score=article_db.relevance_score,
        categories=article_db.categories or [],
        key_points=article_db.key_points or [],
        embedding=embedding,
        is_duplicate=article_db.is_duplicate,
        duplicate_of=article_db.duplicate_of,
    )


def pydantic_to_article_db(article: "Article") -> ArticleDB:
    """
    Convert Pydantic Article to SQLAlchemy ArticleDB model.

    Args:
        article: Pydantic article model.

    Returns:
        ArticleDB: SQLAlchemy article instance.
    """
    import json

    # Convert embedding list to JSON string for storage
    embedding_json = None
    if article.embedding:
        embedding_json = json.dumps(article.embedding)

    return ArticleDB(
        id=article.id,
        source_id=article.source_id,
        source=article.source,
        title=article.title,
        content=article.content,
        url=article.url,
        author=article.author,
        published_at=article.published_at,
        fetched_at=article.fetched_at,
        summary=article.summary,
        relevance_score=article.relevance_score,
        categories=article.categories,
        key_points=article.key_points,
        embedding=embedding_json,
        is_duplicate=article.is_duplicate,
        duplicate_of=article.duplicate_of,
    )
