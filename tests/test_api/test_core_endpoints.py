"""
Tests for core MVP API endpoints.

This module tests the 6 new core API endpoints:
- Search
- Filter
- Enhanced pagination
- Digest list
- Single digest
- Sources metadata
"""

import json
from datetime import datetime, timedelta, date
from uuid import uuid4
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, AsyncMock, patch

from src.models.articles import Article, ArticleSource
from src.main import app
from src.api.dependencies import get_article_repository


@pytest.fixture
def mock_article_repo():
    """Create mock article repository."""
    repo = AsyncMock()
    return repo


@pytest.fixture
def client(mock_article_repo):
    """Create test client with mocked dependencies."""
    app.dependency_overrides[get_article_repository] = lambda: mock_article_repo
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture
def sample_articles():
    """Create sample articles for testing."""
    return [
        Article(
            id=uuid4(),
            source_id="test-1",
            source=ArticleSource.ARXIV,
            title="Transformers: A New Architecture",
            content="Content about transformers and attention mechanisms",
            url="https://arxiv.org/test1",
            published_at=datetime.utcnow() - timedelta(days=1),
            summary="A groundbreaking paper on transformers",
            relevance_score=95.0,
            categories=["research", "nlp"],
            key_points=["Attention is all you need"],
        ),
        Article(
            id=uuid4(),
            source_id="test-2",
            source=ArticleSource.HACKERNEWS,
            title="GPT-4 Released",
            content="OpenAI releases GPT-4 with improved capabilities",
            url="https://news.ycombinator.com/test2",
            published_at=datetime.utcnow() - timedelta(days=2),
            summary="GPT-4 announcement",
            relevance_score=85.0,
            categories=["news", "llm"],
            key_points=["Multimodal capabilities"],
        ),
    ]


class TestSearchEndpoint:
    """Test search API endpoint."""
    
    @pytest.mark.asyncio
    async def test_search_articles_success(self, client, mock_article_repo, sample_articles):
        """Test successful article search."""
        mock_article_repo.search_articles.return_value = (sample_articles, 2)
        
        response = client.get("/api/v1/articles/search?q=transformers")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert data["query"] == "transformers"
        assert len(data["articles"]) == 2
        assert "took_ms" in data
        
    @pytest.mark.asyncio
    async def test_search_with_source_filter(self, client, mock_article_repo, sample_articles):
        """Test search with source filter."""
        filtered = [a for a in sample_articles if a.source == ArticleSource.ARXIV]
        mock_article_repo.search_articles.return_value = (filtered, 1)
        
        response = client.get("/api/v1/articles/search?q=transformers&source=arxiv")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["articles"]) == 1
        
    @pytest.mark.asyncio
    async def test_search_empty_query(self, client):
        """Test search with empty query."""
        response = client.get("/api/v1/articles/search?q=")
        assert response.status_code == 422
        
    @pytest.mark.asyncio
    async def test_search_no_results(self, client, mock_article_repo):
        """Test search with no results."""
        mock_article_repo.search_articles.return_value = ([], 0)
        
        response = client.get("/api/v1/articles/search?q=nonexistent")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert len(data["articles"]) == 0


class TestFilterEndpoint:
    """Test filter API endpoint."""
    
    @pytest.mark.asyncio
    async def test_filter_by_date_range(self, client, mock_article_repo, sample_articles):
        """Test filtering by date range."""
        mock_article_repo.filter_articles.return_value = (sample_articles, 2)
        
        start_date = (datetime.utcnow() - timedelta(days=3)).date()
        end_date = datetime.utcnow().date()
        
        response = client.get(
            f"/api/v1/articles/filter?start_date={start_date}&end_date={end_date}"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert "filters_applied" in data
        assert data["filters_applied"]["start_date"] == str(start_date)
        
    @pytest.mark.asyncio
    async def test_filter_by_relevance(self, client, mock_article_repo, sample_articles):
        """Test filtering by relevance score."""
        filtered = [a for a in sample_articles if a.relevance_score >= 90]
        mock_article_repo.filter_articles.return_value = (filtered, 1)
        
        response = client.get("/api/v1/articles/filter?relevance_min=90")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["filters_applied"]["relevance_min"] == 90
        
    @pytest.mark.asyncio
    async def test_filter_by_sources(self, client, mock_article_repo, sample_articles):
        """Test filtering by multiple sources."""
        mock_article_repo.filter_articles.return_value = (sample_articles, 2)
        
        response = client.get("/api/v1/articles/filter?sources=arxiv,hackernews")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert "sources" in data["filters_applied"]
        
    @pytest.mark.asyncio
    async def test_filter_by_categories(self, client, mock_article_repo, sample_articles):
        """Test filtering by categories."""
        filtered = [a for a in sample_articles if "research" in a.categories]
        mock_article_repo.filter_articles.return_value = (filtered, 1)
        
        response = client.get("/api/v1/articles/filter?categories=research,nlp")
        
        assert response.status_code == 200
        data = response.json()
        assert "categories" in data["filters_applied"]
        
    @pytest.mark.asyncio
    async def test_filter_combined(self, client, mock_article_repo):
        """Test combining multiple filters."""
        mock_article_repo.filter_articles.return_value = ([], 0)
        
        response = client.get(
            "/api/v1/articles/filter"
            "?relevance_min=80&relevance_max=95"
            "&sources=arxiv"
            "&categories=research"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["filters_applied"]) >= 3


class TestPaginatedArticlesEndpoint:
    """Test enhanced pagination endpoint."""
    
    @pytest.mark.asyncio
    async def test_get_articles_page_1(self, client, mock_article_repo, sample_articles):
        """Test getting first page of articles."""
        mock_article_repo.get_articles_paginated.return_value = (sample_articles, 50)
        
        response = client.get("/api/v1/articles?page=1&per_page=20")
        
        assert response.status_code == 200
        data = response.json()
        assert data["pagination"]["page"] == 1
        assert data["pagination"]["per_page"] == 20
        assert data["pagination"]["total"] == 50
        assert data["pagination"]["total_pages"] == 3
        assert data["pagination"]["has_next"] is True
        assert data["pagination"]["has_prev"] is False
        
    @pytest.mark.asyncio
    async def test_get_articles_last_page(self, client, mock_article_repo):
        """Test getting last page of articles."""
        mock_article_repo.get_articles_paginated.return_value = ([], 45)
        
        response = client.get("/api/v1/articles?page=3&per_page=20")
        
        assert response.status_code == 200
        data = response.json()
        assert data["pagination"]["page"] == 3
        assert data["pagination"]["has_next"] is False
        assert data["pagination"]["has_prev"] is True
        
    @pytest.mark.asyncio
    async def test_get_articles_with_sorting(self, client, mock_article_repo, sample_articles):
        """Test articles with custom sorting."""
        mock_article_repo.get_articles_paginated.return_value = (sample_articles, 2)
        
        response = client.get(
            "/api/v1/articles?sort_by=relevance_score&order=desc"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["meta"]["sort_by"] == "relevance_score"
        assert data["meta"]["order"] == "desc"
        
    @pytest.mark.asyncio
    async def test_get_articles_invalid_sort(self, client):
        """Test articles with invalid sort field."""
        response = client.get("/api/v1/articles?sort_by=invalid_field")
        assert response.status_code == 422
        
    @pytest.mark.asyncio
    async def test_get_articles_with_source_filter(self, client, mock_article_repo):
        """Test paginated articles with source filter."""
        mock_article_repo.get_articles_paginated.return_value = ([], 10)
        
        response = client.get("/api/v1/articles?source=arxiv")
        
        assert response.status_code == 200
        mock_article_repo.get_articles_paginated.assert_called_once()


class TestDigestEndpoints:
    """Test digest-related endpoints."""
    
    @pytest.fixture
    def sample_digests(self):
        """Create sample digest data."""
        return [
            {
                "id": str(uuid4()),
                "date": "2025-01-10",
                "title": "AI Daily: January 10, 2025",
                "summary": "Today's AI news summary",
                "key_developments": ["Development 1", "Development 2"],
                "article_count": 15,
                "audio_url": "https://example.com/audio.mp3",
                "audio_duration": 300,
                "created_at": datetime.utcnow().isoformat(),
            }
        ]
    
    @pytest.mark.asyncio
    async def test_get_digests_list(self, client, mock_article_repo, sample_digests):
        """Test getting list of digests."""
        mock_article_repo.get_digests.return_value = (sample_digests, 5)
        
        response = client.get("/api/v1/digests?page=1&per_page=10")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["digests"]) == 1
        assert data["pagination"]["total"] == 5
        assert data["digests"][0]["title"] == sample_digests[0]["title"]
        
    @pytest.mark.asyncio
    async def test_get_digest_by_id(self, client, mock_article_repo):
        """Test getting single digest by ID."""
        digest_id = uuid4()
        digest_data = {
        "id": str(digest_id),
        "date": "2025-01-10",
        "title": "AI Daily: January 10, 2025",
        "summary": "Full digest summary text",
        "key_developments": ["Key point 1", "Key point 2"],
        "articles": [
            {
                "id": str(uuid4()),
                "title": "Article Title",
                "summary": "Article summary",
                "source": "arxiv",
                "url": "https://example.com",
                "relevance_score": 90.0,
            }
        ],
        "audio_url": "https://example.com/audio.mp3",
        "audio_duration": 300,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
        }
        
        mock_article_repo.get_digest_by_id.return_value = digest_data
        
        response = client.get(f"/api/v1/digests/{digest_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(digest_id)
        assert len(data["articles"]) == 1
        assert data["articles"][0]["title"] == "Article Title"
        
    @pytest.mark.asyncio
    async def test_get_digest_not_found(self, client, mock_article_repo):
        """Test getting non-existent digest."""
        digest_id = uuid4()
        
        mock_article_repo.get_digest_by_id.return_value = None
        
        response = client.get(f"/api/v1/digests/{digest_id}")
        
        assert response.status_code == 404
        assert "Digest not found" in response.json()["detail"]
        
    @pytest.mark.asyncio
    async def test_get_digests_empty(self, client, mock_article_repo):
        """Test getting digests when none exist."""
        mock_article_repo.get_digests.return_value = ([], 0)
        
        response = client.get("/api/v1/digests")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["digests"]) == 0
        assert data["pagination"]["total"] == 0


class TestSourcesMetadataEndpoint:
    """Test sources metadata endpoint."""
    
    @pytest.mark.asyncio
    async def test_get_sources_metadata(self, client, mock_article_repo):
        """Test getting sources metadata."""
        sources_data = [
        {
            "name": "arxiv",
            "display_name": "ArXiv",
            "description": "Academic papers and preprints",
            "article_count": 84,
            "last_published": datetime.utcnow().isoformat(),
            "avg_relevance_score": 85.5,
            "status": "active",
            "icon_url": "/icons/arxiv.svg",
        },
        {
            "name": "hackernews",
            "display_name": "Hacker News",
            "description": "Technology and startup news",
            "article_count": 0,
            "last_published": None,
            "avg_relevance_score": 0.0,
            "status": "active",
            "icon_url": "/icons/hackernews.svg",
        },
        ]
        
        mock_article_repo.get_sources_metadata.return_value = sources_data
        mock_article_repo.get_article_stats.return_value = {"total_articles": 211}
        
        with patch("src.api.routes.fetcher_factory") as mock_factory:
            mock_factory.get_health_status.return_value = {
                "fetcher_status": {
                    "arxiv": {"last_request_time": datetime.utcnow().isoformat()},
                    "hackernews": {"last_request_time": None},
                }
            }
            
            response = client.get("/api/v1/sources")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data["sources"]) == 2
            assert data["total_sources"] == 2
            assert data["active_sources"] == 2
            assert data["total_articles"] == 211
            assert data["sources"][0]["name"] == "arxiv"
            assert data["sources"][0]["article_count"] == 84
            
    @pytest.mark.asyncio
    async def test_get_sources_empty(self, client, mock_article_repo):
        """Test getting sources when none are configured."""
        mock_article_repo.get_sources_metadata.return_value = []
        mock_article_repo.get_article_stats.return_value = {"total_articles": 0}
        
        with patch("src.api.routes.fetcher_factory") as mock_factory:
            mock_factory.get_health_status.return_value = {"fetcher_status": {}}
            
            response = client.get("/api/v1/sources")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data["sources"]) == 0
            assert data["total_sources"] == 0


class TestPaginationEdgeCases:
    """Test pagination edge cases."""
    
    @pytest.mark.asyncio
    async def test_page_beyond_total(self, client, mock_article_repo):
        """Test requesting page beyond total pages."""
        mock_article_repo.get_articles_paginated.return_value = ([], 20)
        
        response = client.get("/api/v1/articles?page=100&per_page=20")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["articles"]) == 0
        assert data["pagination"]["page"] == 100
        assert data["pagination"]["has_next"] is False
        
    @pytest.mark.asyncio
    async def test_per_page_limits(self, client, mock_article_repo):
        """Test per_page parameter limits."""
        mock_article_repo.get_articles_paginated.return_value = ([], 100)
        
        # Test max limit
        response = client.get("/api/v1/articles?per_page=200")
        assert response.status_code == 422  # Exceeds max of 100
        
        # Test min limit
        response = client.get("/api/v1/articles?per_page=0")
        assert response.status_code == 422  # Below min of 1
        
    @pytest.mark.asyncio
    async def test_invalid_page_number(self, client):
        """Test invalid page numbers."""
        response = client.get("/api/v1/articles?page=0")
        assert response.status_code == 422
        
        response = client.get("/api/v1/articles?page=-1")
        assert response.status_code == 422


class TestErrorHandling:
    """Test error handling across endpoints."""
    
    @pytest.mark.asyncio
    async def test_repository_error_handling(self, client, mock_article_repo):
        """Test handling of repository errors."""
        mock_article_repo.search_articles.side_effect = Exception("Database error")
        
        response = client.get("/api/v1/articles/search?q=test")
        
        assert response.status_code == 500
        assert "Search operation failed" in response.json()["detail"]
        
    @pytest.mark.asyncio
    async def test_invalid_source_enum(self, client):
        """Test invalid source enum value."""
        response = client.get("/api/v1/articles/search?q=test&source=invalid_source")
        assert response.status_code == 422
        
    @pytest.mark.asyncio
    async def test_invalid_date_format(self, client):
        """Test invalid date format in filter."""
        response = client.get("/api/v1/articles/filter?start_date=invalid-date")
        assert response.status_code == 422
        
    @pytest.mark.asyncio
    async def test_invalid_uuid(self, client):
        """Test invalid UUID for digest endpoint."""
        response = client.get("/api/v1/digests/invalid-uuid")
        assert response.status_code == 422