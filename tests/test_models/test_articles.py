"""
Unit tests for article models.
"""

import pytest
from datetime import datetime
from uuid import uuid4

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.models.articles import Article, ArticleSource, DailyDigest


class TestArticle:
    """Test cases for Article model."""

    def test_article_creation_with_minimal_data(self):
        """Test creating an article with minimal required data."""
        article = Article(
            title="Test Article",
            url="https://example.com/article",
            content="Test content",
            source=ArticleSource.RSS,
            source_id="test-123",
            published_at=datetime.utcnow(),
            author="test@example.com",
            embedding=None,
            is_duplicate=False,
            duplicate_of=None
        )
        
        assert article.title == "Test Article"
        assert article.url == "https://example.com/article"
        assert article.source == ArticleSource.RSS
        assert article.embedding is None
        assert not article.is_duplicate

    def test_article_embedding_validation(self):
        """Test that embedding dimension validation works."""
        # Valid embedding (384 dimensions)
        valid_embedding = [0.1] * 384
        article = Article(
            title="Test Article",
            url="https://example.com/article", 
            content="Test content",
            source=ArticleSource.ARXIV,
            source_id="arxiv-123",
            published_at=datetime.utcnow(),
            author="test@example.com",
            embedding=valid_embedding,
            is_duplicate=False,
            duplicate_of=None
        )
        assert len(article.embedding) == 384

    def test_article_embedding_validation_failure(self):
        """Test that invalid embedding dimension raises error."""
        # Invalid embedding (wrong dimension)
        invalid_embedding = [0.1] * 100
        
        with pytest.raises(ValueError, match="Embedding must have exactly 384 dimensions"):
            Article(
                title="Test Article",
                url="https://example.com/article",
                content="Test content", 
                source=ArticleSource.ARXIV,
                source_id="arxiv-invalid",
                published_at=datetime.utcnow(),
                author="test@example.com",
                embedding=invalid_embedding,
                is_duplicate=False,
                duplicate_of=None
            )


class TestDailyDigest:
    """Test cases for DailyDigest model."""

    def test_daily_digest_creation(self):
        """Test creating a daily digest."""
        digest_date = datetime.utcnow()
        digest = DailyDigest(
            digest_date=digest_date,
            summary_text="Test summary",
            total_articles_processed=5,
            top_articles=[],
            audio_url="https://example.com/audio.mp3"
        )
        
        assert digest.digest_date == digest_date
        assert digest.summary_text == "Test summary"
        assert digest.total_articles_processed == 5
        assert digest.audio_url == "https://example.com/audio.mp3"