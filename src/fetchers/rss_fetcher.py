"""
RSS feed fetcher for AI/ML blogs and news sources.

This module implements fetching from multiple RSS feeds with robust
error handling and date parsing for different feed formats.
"""

import asyncio
import json
import logging
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import feedparser
import httpx

from ..models.articles import Article, ArticleSource
from .base import BaseFetcher, FetchError

logger = logging.getLogger(__name__)


class RSSFetcher(BaseFetcher):
    """
    Fetcher for RSS feeds from AI/ML blogs and news sources.

    Handles multiple RSS feeds with robust error handling and
    graceful degradation if some feeds fail.
    """

    def __init__(self, config_path: str | None = None):
        """Initialize RSS fetcher with feed URLs from configuration file.
        
        Args:
            config_path: Path to RSS feeds configuration file. 
                        If None, uses default path 'config/rss_feeds.json'
        """
        super().__init__(source=ArticleSource.RSS, rate_limit_delay=2.0)

        # Set config path
        if config_path is None:
            # Get project root directory (where main.py is located)
            project_root = Path(__file__).parent.parent.parent
            self.config_path = project_root / "config" / "rss_feeds.json"
        else:
            self.config_path = Path(config_path)
        self.feed_urls: dict[str, str] = {}
        self.timeout = 10.0  # 10 second timeout per feed

        # Load feeds from configuration
        self._load_feeds_from_config()

        logger.info(f"RSS fetcher initialized with {len(self.feed_urls)} feeds")

    async def fetch(self, max_articles: int = 100) -> list[Article]:
        """
        Fetch articles from all RSS feeds.

        Args:
            max_articles: Maximum total articles to return.

        Returns:
            List[Article]: Articles from all feeds combined.

        Raises:
            FetchError: If all feeds fail to fetch.
        """
        try:
            logger.info(f"Fetching from {len(self.feed_urls)} RSS feeds")

            # Fetch all feeds concurrently
            all_articles: list[Article] = []
            successful_feeds = 0
            failed_feeds = []

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                tasks = []
                for feed_name, feed_url in self.feed_urls.items():
                    task = self._fetch_single_feed(client, feed_name, feed_url)
                    tasks.append(task)

                results = await asyncio.gather(*tasks, return_exceptions=True)

                for i, result in enumerate(results):
                    feed_name = list(self.feed_urls.keys())[i]

                    if isinstance(result, Exception):
                        logger.warning(f"Failed to fetch {feed_name}: {result}")
                        failed_feeds.append(feed_name)
                    else:
                        articles, success = result
                        if success:
                            all_articles.extend(articles)
                            successful_feeds += 1
                            logger.debug(f"Fetched {len(articles)} articles from {feed_name}")
                        else:
                            failed_feeds.append(feed_name)

            if successful_feeds == 0:
                raise FetchError("All RSS feeds failed to fetch")

            # Sort by published date (newest first) and limit
            all_articles.sort(key=lambda x: x.published_at, reverse=True)
            limited_articles = all_articles[:max_articles]

            logger.info(
                f"Successfully fetched {len(limited_articles)} articles from "
                f"{successful_feeds}/{len(self.feed_urls)} feeds"
            )

            if failed_feeds:
                logger.warning(f"Failed feeds: {', '.join(failed_feeds)}")

            return limited_articles

        except Exception as e:
            error_msg = f"Failed to fetch RSS feeds: {str(e)}"
            logger.error(error_msg)
            raise FetchError(error_msg, source=self.source)

    async def _fetch_single_feed(
        self,
        client: httpx.AsyncClient,
        feed_name: str,
        feed_url: str
    ) -> tuple[list[Article], bool]:
        """
        Fetch articles from a single RSS feed.

        Args:
            client: HTTP client for requests.
            feed_name: Human-readable feed name.
            feed_url: URL of the RSS feed.

        Returns:
            Tuple[List[Article], bool]: Articles and success flag.
        """
        try:
            # Apply rate limiting
            await self._apply_rate_limit()

            # Fetch feed content
            response = await client.get(feed_url)
            response.raise_for_status()

            # Parse with feedparser
            feed_content = response.text
            feed = feedparser.parse(feed_content)

            if feed.bozo and hasattr(feed, 'bozo_exception'):
                logger.warning(f"Feed parsing warning for {feed_name}: {feed.bozo_exception}")

            # Convert entries to articles
            articles = []
            for entry in feed.entries:
                try:
                    article = self._convert_entry_to_article(entry, feed_name, feed_url)
                    if article:
                        articles.append(article)
                except Exception as e:
                    logger.warning(f"Failed to convert entry from {feed_name}: {e}")
                    continue

            return articles, True

        except Exception as e:
            logger.error(f"Failed to fetch {feed_name} ({feed_url}): {e}")
            return [], False

    def _convert_entry_to_article(
        self,
        entry: feedparser.FeedParserDict,
        feed_name: str,
        feed_url: str
    ) -> Article | None:
        """
        Convert RSS entry to Article model.

        Args:
            entry: RSS feed entry.
            feed_name: Name of the source feed.
            feed_url: URL of the source feed.

        Returns:
            Article: Converted article, or None if conversion fails.
        """
        # Extract title
        title = entry.get('title', '').strip()
        if not title:
            return None

        # Extract URL
        url = entry.get('link', '')
        if not url:
            return None

        # Extract content (try multiple fields)
        content = ''
        if hasattr(entry, 'content') and entry.content:
            # Try content field first
            content = entry.content[0].value if isinstance(entry.content, list) else entry.content
        elif entry.get('summary'):
            # Fall back to summary
            content = entry.summary
        elif entry.get('description'):
            # Fall back to description
            content = entry.description
        else:
            # Use title as content if nothing else available
            content = title

        # Clean HTML tags from content
        import re
        content = re.sub(r'<[^>]+>', '', content)
        content = content.strip()

        # Extract author
        author = entry.get('author', '') or feed_name

        # Extract and parse published date
        published_at = self._parse_entry_date(entry)
        if not published_at:
            # Use current time if no date available
            published_at = datetime.now(UTC)

        # Create unique source ID
        source_id = self._generate_source_id(entry, url)

        # Determine if this is a YouTube video and extract metadata
        is_youtube = self._is_youtube_feed(feed_url, url)
        article_source = ArticleSource.YOUTUBE if is_youtube else ArticleSource.RSS
        metadata = {}

        if is_youtube:
            metadata = self._extract_youtube_metadata(entry, feed_name)

        return Article(
            source_id=source_id,
            source=article_source,
            title=title,
            content=content,
            url=url,
            author=author,
            published_at=published_at,
            fetched_at=datetime.now(UTC),
            metadata=metadata,
            summary=None,
            relevance_score=None,
            embedding=None,
            is_duplicate=False,
            duplicate_of=None
        )

    def _parse_entry_date(self, entry: feedparser.FeedParserDict) -> datetime | None:
        """
        Parse date from RSS entry with multiple fallbacks.

        Args:
            entry: RSS feed entry.

        Returns:
            datetime: Parsed date, or None if parsing fails.
        """
        # Try different date fields and formats
        date_fields = ['published_parsed', 'updated_parsed', 'created_parsed']

        for field in date_fields:
            if hasattr(entry, field) and getattr(entry, field):
                try:
                    time_struct = getattr(entry, field)
                    if time_struct:
                        return datetime(*time_struct[:6])
                except (TypeError, ValueError) as e:
                    logger.debug(f"Failed to parse {field}: {e}")
                    continue

        # Try string date fields
        string_date_fields = ['published', 'updated', 'created']
        for field in string_date_fields:
            date_str = entry.get(field)
            if date_str:
                try:
                    # feedparser usually handles this, but try manual parsing as fallback
                    from email.utils import parsedate_to_datetime
                    return parsedate_to_datetime(date_str)
                except Exception as e:
                    logger.debug(f"Failed to parse date string '{date_str}': {e}")
                    continue

        return None

    def _generate_source_id(self, entry: feedparser.FeedParserDict, url: str) -> str:
        """
        Generate a unique source ID for the entry.

        Args:
            entry: RSS feed entry.
            url: Entry URL.

        Returns:
            str: Unique source identifier.
        """
        # Try to use entry ID if available
        if entry.get('id'):
            return entry.id

        # Try to use GUID if available
        if entry.get('guid'):
            return entry.guid

        # Fall back to URL hash
        import hashlib
        return hashlib.md5(url.encode()).hexdigest()

    async def fetch_recent(self, hours: int = 24) -> list[Article]:
        """
        Fetch recent articles from the last N hours.

        Args:
            hours: Number of hours to look back.

        Returns:
            List[Article]: Recent articles.
        """
        cutoff_date = datetime.now(UTC) - timedelta(hours=hours)

        # Fetch all articles and filter by date
        articles = await self.fetch(max_articles=500)  # Fetch more to account for filtering

        recent_articles = [
            article for article in articles
            if article.published_at >= cutoff_date
        ]

        logger.info(f"Found {len(recent_articles)} recent articles from last {hours} hours")
        return recent_articles

    def get_feed_urls(self) -> dict[str, str]:
        """
        Get mapping of feed names to URLs.

        Returns:
            Dict[str, str]: Feed name to URL mapping.
        """
        return self.feed_urls.copy()

    def _load_feeds_from_config(self) -> None:
        """
        Load RSS feed URLs from configuration file.
        
        Creates default config if file doesn't exist.
        """
        if not self.config_path.exists():
            logger.warning(f"RSS config file not found at {self.config_path}, creating default")
            self._create_default_config()

        try:
            with open(self.config_path) as f:
                config = json.load(f)

            # Flatten nested feed structure into single dict
            self.feed_urls = {}
            feeds = config.get('feeds', {})

            for category, category_feeds in feeds.items():
                if isinstance(category_feeds, dict):
                    self.feed_urls.update(category_feeds)
                else:
                    logger.warning(f"Invalid feed category format: {category}")

            logger.info(f"Loaded {len(self.feed_urls)} RSS feeds from {self.config_path}")

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse RSS config file: {e}")
            logger.info("Using empty feed list")
            self.feed_urls = {}
        except Exception as e:
            logger.error(f"Failed to load RSS config: {e}")
            logger.info("Using empty feed list")
            self.feed_urls = {}

    def _create_default_config(self) -> None:
        """Create default RSS feeds configuration file."""
        default_config = {
            "feeds": {
                "company_blogs": {
                    "OpenAI Blog": "https://openai.com/index/rss.xml",
                    "Anthropic Blog": "https://www.anthropic.com/index.xml",
                    "Google AI Blog": "https://ai.googleblog.com/feeds/posts/default",
                    "Hugging Face Blog": "https://huggingface.co/blog/feed.xml",
                    "Meta AI Research": "https://ai.facebook.com/blog/rss/",
                    "DeepMind Blog": "https://deepmind.com/blog/rss/",
                    "Microsoft Research AI": "https://www.microsoft.com/en-us/research/feed/"
                },
                "tech_news": {
                    "TechCrunch AI": "https://techcrunch.com/category/artificial-intelligence/feed/",
                    "The Verge AI": "https://www.theverge.com/ai-artificial-intelligence/rss/index.xml",
                    "VentureBeat AI": "https://venturebeat.com/ai/feed/",
                    "MIT Technology Review AI": "https://www.technologyreview.com/topic/artificial-intelligence/feed/"
                },
                "cloud_providers": {
                    "AWS Machine Learning Blog": "https://aws.amazon.com/blogs/machine-learning/feed/",
                    "Google Cloud AI Blog": "https://cloud.google.com/blog/topics/ai-machine-learning/rss"
                }
            }
        }

        # Ensure config directory exists
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(self.config_path, 'w') as f:
                json.dump(default_config, f, indent=2)
            logger.info(f"Created default RSS config at {self.config_path}")
        except Exception as e:
            logger.error(f"Failed to create default config: {e}")

    def add_feed(self, name: str, url: str, category: str = "custom") -> None:
        """
        Add a new RSS feed and persist to configuration.

        Args:
            name: Human-readable feed name.
            url: RSS feed URL.
            category: Category to add the feed under (default: "custom")
        """
        # Validate URL format
        if not self._validate_feed_url(url):
            raise ValueError(f"Invalid RSS feed URL: {url}")

        # Add to in-memory feed list
        self.feed_urls[name] = url

        # Update configuration file
        self._update_config_file(name, url, category, action="add")

        logger.info(f"Added RSS feed: {name} ({url}) to category '{category}'")

    def remove_feed(self, name: str) -> bool:
        """
        Remove an RSS feed and update configuration.

        Args:
            name: Feed name to remove.

        Returns:
            bool: True if feed was removed, False if not found.
        """
        if name in self.feed_urls:
            # Remove from in-memory list
            del self.feed_urls[name]

            # Update configuration file
            self._update_config_file(name, None, None, action="remove")

            logger.info(f"Removed RSS feed: {name}")
            return True
        return False

    def _validate_feed_url(self, url: str) -> bool:
        """
        Validate that the URL looks like a valid RSS feed URL.
        
        Args:
            url: URL to validate
            
        Returns:
            bool: True if URL appears valid
        """
        if not url or not isinstance(url, str):
            return False

        # Check basic URL format
        if not (url.startswith("http://") or url.startswith("https://")):
            return False

        # Check for common RSS indicators
        rss_indicators = [".xml", ".rss", "/feed", "/rss", "feed/", "rss/"]
        url_lower = url.lower()

        # Allow any URL but warn if it doesn't look like RSS
        has_rss_indicator = any(indicator in url_lower for indicator in rss_indicators)
        if not has_rss_indicator:
            logger.warning(f"URL '{url}' doesn't contain common RSS indicators, but allowing it")

        return True

    def _update_config_file(self, name: str, url: str | None, category: str | None, action: str) -> None:
        """
        Update the configuration file with feed changes.
        
        Args:
            name: Feed name
            url: Feed URL (None for removal)
            category: Feed category (None for removal)
            action: "add" or "remove"
        """
        try:
            # Load current config
            config = {}
            if self.config_path.exists():
                with open(self.config_path) as f:
                    config = json.load(f)

            feeds = config.get('feeds', {})

            if action == "add":
                # Ensure category exists
                if category not in feeds:
                    feeds[category] = {}

                # Add feed to category
                feeds[category][name] = url

            elif action == "remove":
                # Find and remove feed from any category
                for cat_name, cat_feeds in feeds.items():
                    if isinstance(cat_feeds, dict) and name in cat_feeds:
                        del cat_feeds[name]
                        # Remove empty categories
                        if not cat_feeds and cat_name != "custom":
                            del feeds[cat_name]
                        break

            # Save updated config
            config['feeds'] = feeds

            # Ensure directory exists
            self.config_path.parent.mkdir(parents=True, exist_ok=True)

            with open(self.config_path, 'w') as f:
                json.dump(config, f, indent=2)

            logger.debug(f"Updated RSS config file: {action} feed '{name}'")

        except Exception as e:
            logger.error(f"Failed to update RSS config file: {e}")
            # Continue anyway - in-memory update was successful

    def _is_youtube_feed(self, feed_url: str, article_url: str) -> bool:
        """
        Determine if this is a YouTube RSS feed.
        
        Args:
            feed_url: URL of the RSS feed.
            article_url: URL of the article.
            
        Returns:
            bool: True if this is a YouTube feed.
        """
        return ('youtube.com/feeds/videos.xml' in feed_url or
                'youtube.com/watch' in article_url or
                'youtu.be/' in article_url)

    def _extract_youtube_metadata(
        self,
        entry: feedparser.FeedParserDict,
        channel_name: str
    ) -> dict[str, Any]:
        """
        Extract YouTube-specific metadata from RSS entry.
        
        Args:
            entry: RSS feed entry.
            channel_name: Name of the YouTube channel.
            
        Returns:
            dict: YouTube-specific metadata.
        """
        metadata = {
            "channel": channel_name,
            "platform": "youtube"
        }

        # Extract video ID from URL
        url = entry.get('link', '')
        if 'youtube.com/watch?v=' in url:
            video_id = url.split('v=')[1].split('&')[0]
            metadata["video_id"] = video_id
        elif 'youtu.be/' in url:
            video_id = url.split('youtu.be/')[1].split('?')[0]
            metadata["video_id"] = video_id

        # Extract duration from media:group/yt:duration if available
        if hasattr(entry, 'yt_duration'):
            metadata["duration"] = entry.yt_duration

        # Extract view count if available in media:group/media:community
        if hasattr(entry, 'media_statistics'):
            metadata["views"] = getattr(entry.media_statistics, 'views', None)

        # Extract thumbnail URL
        if hasattr(entry, 'media_thumbnail'):
            thumbnails = entry.media_thumbnail if isinstance(entry.media_thumbnail, list) else [entry.media_thumbnail]
            if thumbnails:
                metadata["thumbnail_url"] = thumbnails[0].get('url', '')

        return metadata
