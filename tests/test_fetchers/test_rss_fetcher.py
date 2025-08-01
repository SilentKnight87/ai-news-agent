"""
Tests for RSS feed fetcher with configuration file support.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import feedparser
import pytest

from src.fetchers.rss_fetcher import RSSFetcher
from src.models.articles import ArticleSource


class TestRSSFetcher:
    """Test cases for RSS fetcher configuration."""

    @pytest.fixture
    def temp_config_dir(self):
        """Create a temporary directory for test configs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def sample_config(self, temp_config_dir):
        """Create a sample RSS config file."""
        config_path = temp_config_dir / "rss_feeds.json"
        config_data = {
            "feeds": {
                "test_category": {
                    "Test Feed 1": "https://example.com/feed1.xml",
                    "Test Feed 2": "https://example.com/feed2.rss"
                }
            }
        }
        with open(config_path, 'w') as f:
            json.dump(config_data, f)
        return config_path

    def test_init_loads_config_file(self, sample_config):
        """Test that RSS fetcher loads feeds from config file."""
        fetcher = RSSFetcher(config_path=str(sample_config))
        
        assert len(fetcher.feed_urls) == 2
        assert "Test Feed 1" in fetcher.feed_urls
        assert "Test Feed 2" in fetcher.feed_urls
        assert fetcher.feed_urls["Test Feed 1"] == "https://example.com/feed1.xml"

    def test_init_creates_default_config_if_missing(self, temp_config_dir):
        """Test that default config is created if file doesn't exist."""
        config_path = temp_config_dir / "rss_feeds.json"
        fetcher = RSSFetcher(config_path=str(config_path))
        
        # Check that config file was created
        assert config_path.exists()
        
        # Check that default feeds were loaded
        assert len(fetcher.feed_urls) > 0
        assert "OpenAI Blog" in fetcher.feed_urls

    def test_add_feed_updates_config(self, sample_config):
        """Test that adding a feed updates the config file."""
        fetcher = RSSFetcher(config_path=str(sample_config))
        
        # Add new feed
        fetcher.add_feed("New Feed", "https://example.com/new.xml", "new_category")
        
        # Check in-memory update
        assert "New Feed" in fetcher.feed_urls
        
        # Check config file update
        with open(sample_config, 'r') as f:
            config = json.load(f)
        
        assert "new_category" in config["feeds"]
        assert "New Feed" in config["feeds"]["new_category"]
        assert config["feeds"]["new_category"]["New Feed"] == "https://example.com/new.xml"

    def test_remove_feed_updates_config(self, sample_config):
        """Test that removing a feed updates the config file."""
        fetcher = RSSFetcher(config_path=str(sample_config))
        
        # Remove existing feed
        result = fetcher.remove_feed("Test Feed 1")
        
        assert result is True
        assert "Test Feed 1" not in fetcher.feed_urls
        
        # Check config file update
        with open(sample_config, 'r') as f:
            config = json.load(f)
        
        assert "Test Feed 1" not in config["feeds"]["test_category"]

    def test_remove_nonexistent_feed(self, sample_config):
        """Test removing a feed that doesn't exist."""
        fetcher = RSSFetcher(config_path=str(sample_config))
        
        result = fetcher.remove_feed("Nonexistent Feed")
        assert result is False

    def test_validate_feed_url(self, temp_config_dir):
        """Test URL validation."""
        config_path = temp_config_dir / "rss_feeds.json"
        fetcher = RSSFetcher(config_path=str(config_path))
        
        # Valid URLs
        assert fetcher._validate_feed_url("https://example.com/feed.xml")
        assert fetcher._validate_feed_url("http://example.com/rss")
        assert fetcher._validate_feed_url("https://example.com/blog/feed/")
        
        # Invalid URLs
        assert not fetcher._validate_feed_url("")
        assert not fetcher._validate_feed_url(None)
        assert not fetcher._validate_feed_url("not-a-url")
        assert not fetcher._validate_feed_url("ftp://example.com/feed.xml")

    def test_add_feed_validates_url(self, sample_config):
        """Test that add_feed validates URLs."""
        fetcher = RSSFetcher(config_path=str(sample_config))
        
        # Invalid URL should raise ValueError
        with pytest.raises(ValueError, match="Invalid RSS feed URL"):
            fetcher.add_feed("Bad Feed", "not-a-url")

    def test_config_file_corruption_handling(self, temp_config_dir):
        """Test handling of corrupted config file."""
        config_path = temp_config_dir / "rss_feeds.json"
        
        # Create corrupted config file
        with open(config_path, 'w') as f:
            f.write("{ invalid json")
        
        # Should handle gracefully and use empty feed list
        fetcher = RSSFetcher(config_path=str(config_path))
        assert fetcher.feed_urls == {}

    def test_nested_category_structure(self, temp_config_dir):
        """Test that nested category structure is properly flattened."""
        config_path = temp_config_dir / "rss_feeds.json"
        config_data = {
            "feeds": {
                "category1": {
                    "Feed A": "https://a.com/feed.xml",
                    "Feed B": "https://b.com/feed.xml"
                },
                "category2": {
                    "Feed C": "https://c.com/feed.xml"
                }
            }
        }
        
        with open(config_path, 'w') as f:
            json.dump(config_data, f)
        
        fetcher = RSSFetcher(config_path=str(config_path))
        
        # All feeds should be flattened into single dict
        assert len(fetcher.feed_urls) == 3
        assert "Feed A" in fetcher.feed_urls
        assert "Feed B" in fetcher.feed_urls
        assert "Feed C" in fetcher.feed_urls

    @pytest.mark.asyncio
    async def test_fetch_with_config_feeds(self, sample_config):
        """Test fetching articles from configured feeds."""
        fetcher = RSSFetcher(config_path=str(sample_config))
        
        # Mock the HTTP client and feedparser
        mock_response = MagicMock()
        mock_response.text = "<rss>mock feed content</rss>"
        mock_response.raise_for_status = MagicMock()
        
        # Create a proper feedparser-like structure
        mock_feed = MagicMock()
        mock_feed.bozo = False
        
        # Create mock entry with feedparser structure
        mock_entry = MagicMock()
        # Configure get method for the entry
        mock_entry.get.side_effect = lambda key, default='': {
            'title': 'Test Article',
            'link': 'https://example.com/article', 
            'summary': 'Test content',
            'author': 'Test Author',
            'id': 'test-id',
            'guid': 'test-guid',
            'description': 'Test content'
        }.get(key, default)
        
        # Set string attributes directly 
        mock_entry.summary = 'Test content'
        mock_entry.description = 'Test content'
        mock_entry.id = 'test-id'
        mock_entry.guid = 'test-guid'
        
        # Ensure hasattr works properly for our mock
        mock_entry.published_parsed = (2024, 1, 1, 0, 0, 0, 0, 0, 0)
        mock_entry.content = None
        
        mock_feed.entries = [mock_entry]
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            with patch('feedparser.parse', return_value=mock_feed):
                articles = await fetcher.fetch(max_articles=10)
        
        assert len(articles) == 2  # Two feeds, one article each
        assert all(article.source == ArticleSource.RSS for article in articles)
        assert all(article.title == 'Test Article' for article in articles)