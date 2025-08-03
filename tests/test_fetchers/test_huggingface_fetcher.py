"""
Tests for HuggingFace models fetcher.
"""

from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest

from src.fetchers.huggingface_fetcher import HuggingFaceFetcher
from src.models.articles import ArticleSource


class TestHuggingFaceFetcher:
    """Test cases for HuggingFace models fetcher."""

    @pytest.fixture
    def sample_models_response(self):
        """Sample response from HuggingFace models API."""
        return [
            {
                "id": "microsoft/DialoGPT-medium",
                "downloads": 12500,
                "likes": 150,
                "tags": ["text-generation", "conversational", "pytorch"],
                "description": "A conversational AI model based on GPT-2",
                "lastModified": "2024-01-15T10:30:45Z",
                "cardData": {
                    "license": "MIT",
                    "base_model": "gpt2"
                },
                "pipeline_tag": "text-generation"
            },
            {
                "id": "bert-base-uncased",
                "downloads": 50000,
                "likes": 300,
                "tags": ["fill-mask", "feature-extraction", "pytorch"],
                "description": "BERT base model (uncased)",
                "lastModified": "2024-01-10T08:15:30Z",
                "cardData": {
                    "license": "Apache-2.0"
                },
                "pipeline_tag": "fill-mask"
            },
            {
                "id": "irrelevant/dataset-model",
                "downloads": 100,
                "likes": 5,
                "tags": ["dataset", "text"],
                "description": "A dataset, not a model",
                "lastModified": "2024-01-05T12:00:00Z"
            }
        ]

    @pytest.fixture
    def fetcher(self):
        """Create HuggingFace fetcher instance."""
        return HuggingFaceFetcher()

    @pytest.fixture
    def fetcher_with_key(self):
        """Create HuggingFace fetcher with API key."""
        return HuggingFaceFetcher(hf_api_key="test_key")

    def test_initialization_without_key(self, fetcher):
        """Test fetcher initialization without API key."""
        assert fetcher.source == ArticleSource.HUGGINGFACE
        assert fetcher.rate_limit_delay == 0.1
        assert fetcher.base_url == "https://huggingface.co/api"
        assert "Authorization" not in fetcher.headers

    def test_initialization_with_key(self, fetcher_with_key):
        """Test fetcher initialization with API key."""
        assert "Authorization" in fetcher_with_key.headers
        assert fetcher_with_key.headers["Authorization"] == "Bearer test_key"

    @pytest.mark.asyncio
    async def test_fetch_trending_models(self, fetcher, sample_models_response):
        """Test fetching trending models."""
        mock_response = MagicMock()
        mock_response.json.return_value = sample_models_response

        with patch.object(fetcher.client, 'get', return_value=mock_response) as mock_get:
            result = await fetcher._fetch_trending_models()

            mock_get.assert_called_once_with(
                "https://huggingface.co/api/models",
                params={"sort": "trending", "limit": 25, "full": "true"},
                headers=fetcher.headers
            )
            assert result == sample_models_response

    @pytest.mark.asyncio
    async def test_fetch_new_models(self, fetcher, sample_models_response):
        """Test fetching new models."""
        mock_response = MagicMock()
        mock_response.json.return_value = sample_models_response

        with patch.object(fetcher.client, 'get', return_value=mock_response) as mock_get:
            result = await fetcher._fetch_new_models()

            mock_get.assert_called_once_with(
                "https://huggingface.co/api/models",
                params={"sort": "lastModified", "limit": 25, "full": "true"},
                headers=fetcher.headers
            )
            assert result == sample_models_response

    def test_is_relevant_model_text_generation(self, fetcher):
        """Test relevance check for text generation model."""
        model = {
            "id": "test/model",
            "tags": ["text-generation"],
            "downloads": 100
        }
        assert fetcher._is_relevant_model(model) is True

    def test_is_relevant_model_high_downloads(self, fetcher):
        """Test relevance check for high-download model."""
        model = {
            "id": "test/model",
            "tags": ["unknown-tag"],
            "downloads": 5000
        }
        assert fetcher._is_relevant_model(model) is True

    def test_is_relevant_model_dataset_excluded(self, fetcher):
        """Test that datasets are excluded."""
        model = {
            "id": "test/dataset",
            "tags": ["dataset", "text-generation"],
            "downloads": 5000
        }
        assert fetcher._is_relevant_model(model) is False

    def test_is_relevant_model_irrelevant(self, fetcher):
        """Test irrelevant model filtering."""
        model = {
            "id": "test/model",
            "tags": ["audio", "music"],
            "downloads": 50
        }
        assert fetcher._is_relevant_model(model) is False

    def test_model_to_article(self, fetcher, sample_models_response):
        """Test converting model data to article."""
        model = sample_models_response[0]
        article = fetcher._model_to_article(model)

        assert article is not None
        assert article.source == ArticleSource.HUGGINGFACE
        assert article.title == "🤗 microsoft/DialoGPT-medium"
        assert "conversational AI model" in article.content
        assert article.url == "https://huggingface.co/microsoft/DialoGPT-medium"
        assert article.author == "microsoft"
        assert article.source_id == "microsoft/DialoGPT-medium"

        # Check metadata
        assert article.metadata["platform"] == "huggingface"
        assert article.metadata["model_id"] == "microsoft/DialoGPT-medium"
        assert article.metadata["downloads"] == 12500
        assert article.metadata["likes"] == 150
        assert article.metadata["license"] == "MIT"
        assert article.metadata["base_model"] == "gpt2"
        assert article.metadata["pipeline_tag"] == "text-generation"

    def test_model_to_article_minimal_data(self, fetcher):
        """Test converting model with minimal data."""
        model = {
            "id": "test/minimal-model",
            "tags": ["text-generation"],
            "downloads": 100
        }

        article = fetcher._model_to_article(model)

        assert article is not None
        assert article.title == "🤗 test/minimal-model"
        assert "AI model for text-generation" in article.content
        assert article.author == "test"

    def test_model_to_article_no_id(self, fetcher):
        """Test converting model without ID returns None."""
        model = {"tags": ["text-generation"]}
        article = fetcher._model_to_article(model)
        assert article is None

    def test_parse_model_date(self, fetcher):
        """Test parsing model dates."""
        model = {"lastModified": "2024-01-15T10:30:45Z"}
        date = fetcher._parse_model_date(model)

        expected = datetime(2024, 1, 15, 10, 30, 45, tzinfo=UTC)
        assert date == expected

    def test_parse_model_date_invalid(self, fetcher):
        """Test parsing invalid model date falls back to current time."""
        model = {"lastModified": "invalid-date"}
        date = fetcher._parse_model_date(model)

        # Should be recent (within last minute)
        now = datetime.now(UTC)
        assert abs((now - date).total_seconds()) < 60

    def test_parse_model_date_missing(self, fetcher):
        """Test parsing missing model date falls back to current time."""
        model = {}
        date = fetcher._parse_model_date(model)

        # Should be recent (within last minute)
        now = datetime.now(UTC)
        assert abs((now - date).total_seconds()) < 60

    def test_extract_model_metadata(self, fetcher, sample_models_response):
        """Test extracting model metadata."""
        model = sample_models_response[0]
        metadata = fetcher._extract_model_metadata(model)

        assert metadata["platform"] == "huggingface"
        assert metadata["model_id"] == "microsoft/DialoGPT-medium"
        assert metadata["downloads"] == 12500
        assert metadata["likes"] == 150
        assert metadata["tags"] == ["text-generation", "conversational", "pytorch"]
        assert metadata["license"] == "MIT"
        assert metadata["base_model"] == "gpt2"
        assert metadata["pipeline_tag"] == "text-generation"
        assert metadata["trending"] is True  # High downloads

    def test_extract_model_metadata_minimal(self, fetcher):
        """Test extracting metadata from minimal model data."""
        model = {
            "id": "test/model",
            "downloads": 50,
            "likes": 2,
            "tags": []
        }

        metadata = fetcher._extract_model_metadata(model)

        assert metadata["platform"] == "huggingface"
        assert metadata["model_id"] == "test/model"
        assert metadata["downloads"] == 50
        assert metadata["likes"] == 2
        assert metadata["tags"] == []
        assert "trending" not in metadata  # Low activity

    @pytest.mark.asyncio
    async def test_fetch_success(self, fetcher, sample_models_response):
        """Test successful fetching of models."""
        mock_response = MagicMock()
        mock_response.json.return_value = sample_models_response

        with patch.object(fetcher.client, 'get', return_value=mock_response):
            articles = await fetcher.fetch(max_articles=10)

            # Should return 2 articles (excluding the dataset)
            assert len(articles) == 2
            assert all(article.source == ArticleSource.HUGGINGFACE for article in articles)

            # Should be sorted by downloads (highest first)
            assert articles[0].metadata["downloads"] >= articles[1].metadata["downloads"]

    @pytest.mark.asyncio
    async def test_fetch_with_exceptions(self, fetcher):
        """Test fetching with partial failures."""
        # Mock one successful and one failed response
        trending_response = MagicMock()
        trending_response.json.return_value = [{
            "id": "test/model",
            "downloads": 1000,
            "likes": 50,
            "tags": ["text-generation"]
        }]

        with patch.object(fetcher, '_fetch_trending_models', return_value=trending_response.json.return_value), \
             patch.object(fetcher, '_fetch_new_models', side_effect=Exception("API Error")):

            articles = await fetcher.fetch()

            # Should still return articles from successful stream
            assert len(articles) == 1
            assert articles[0].source_id == "test/model"

    @pytest.mark.asyncio
    async def test_fetch_no_relevant_models(self, fetcher):
        """Test fetching when no models are relevant."""
        irrelevant_models = [{
            "id": "test/dataset",
            "downloads": 100,
            "tags": ["dataset"]
        }]

        mock_response = MagicMock()
        mock_response.json.return_value = irrelevant_models

        with patch.object(fetcher.client, 'get', return_value=mock_response):
            articles = await fetcher.fetch()

            assert len(articles) == 0

    @pytest.mark.asyncio
    async def test_fetch_error_handling(self, fetcher):
        """Test error handling during fetch."""
        with patch.object(fetcher.client, 'get', side_effect=Exception("API Error")):
            # Individual API failures are handled gracefully, only general errors raise FetchError
            articles = await fetcher.fetch(max_articles=10)
            # Should return empty list when all API calls fail
            assert articles == []

    @pytest.mark.asyncio
    async def test_fetch_with_rate_limiting(self, fetcher):
        """Test that rate limiting is handled by RateLimitedHTTPClient."""
        mock_response = MagicMock()
        mock_response.json.return_value = []

        with patch.object(fetcher.client, 'get', return_value=mock_response) as mock_get:
            await fetcher._fetch_trending_models()

            # Verify that the client.get method was called (rate limiting is handled internally)
            mock_get.assert_called_once()

    def test_metadata_trending_detection(self, fetcher):
        """Test trending detection in metadata."""
        # High downloads model
        high_downloads_model = {
            "id": "test/popular",
            "downloads": 15000,
            "likes": 50
        }
        metadata = fetcher._extract_model_metadata(high_downloads_model)
        assert metadata["trending"] is True

        # High likes model
        high_likes_model = {
            "id": "test/liked",
            "downloads": 500,
            "likes": 150
        }
        metadata = fetcher._extract_model_metadata(high_likes_model)
        assert metadata["trending"] is True

        # Low activity model
        low_activity_model = {
            "id": "test/quiet",
            "downloads": 50,
            "likes": 5
        }
        metadata = fetcher._extract_model_metadata(low_activity_model)
        assert "trending" not in metadata
