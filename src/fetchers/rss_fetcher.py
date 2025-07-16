"""
RSS feed fetcher for AI/ML blogs and news sources.

This module implements fetching from multiple RSS feeds with robust
error handling and date parsing for different feed formats.
"""

import asyncio
import logging
from datetime import datetime, timedelta

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

    def __init__(self):
        """Initialize RSS fetcher with feed URLs."""
        super().__init__(source=ArticleSource.RSS, rate_limit_delay=2.0)

        # MVP RSS feeds from INITIAL.md
        self.feed_urls = {
            # Company blogs
            "OpenAI Blog": "https://openai.com/index/rss.xml",
            "Anthropic Blog": "https://www.anthropic.com/index.xml",
            "Google AI Blog": "https://ai.googleblog.com/feeds/posts/default",
            "Hugging Face Blog": "https://huggingface.co/blog/feed.xml",
            "Meta AI Research": "https://ai.facebook.com/blog/rss/",
            "DeepMind Blog": "https://deepmind.com/blog/rss/",
            "Microsoft Research AI": "https://www.microsoft.com/en-us/research/feed/",

            # Academic and research
            "MIT CSAIL News": "https://www.csail.mit.edu/news/rss.xml",
            "Papers with Code": "https://paperswithcode.com/latest.rss",

            # Industry news
            "TechCrunch AI": "https://techcrunch.com/category/artificial-intelligence/feed/",
            "The Verge AI": "https://www.theverge.com/ai-artificial-intelligence/rss/index.xml",
            "VentureBeat AI": "https://venturebeat.com/ai/feed/",
            "MIT Technology Review AI": "https://www.technologyreview.com/topic/artificial-intelligence/feed/",

            # Cloud providers
            "AWS Machine Learning Blog": "https://aws.amazon.com/blogs/machine-learning/feed/",
            "Google Cloud AI Blog": "https://cloud.google.com/blog/topics/ai-machine-learning/rss",
        }

        self.timeout = 10.0  # 10 second timeout per feed

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
            all_articles = []
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
            published_at = datetime.utcnow()

        # Create unique source ID
        source_id = self._generate_source_id(entry, url)

        return Article(
            source_id=source_id,
            source=ArticleSource.RSS,
            title=title,
            content=content,
            url=url,
            author=author,
            published_at=published_at,
            fetched_at=datetime.utcnow()
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
        cutoff_date = datetime.utcnow() - timedelta(hours=hours)

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

    def add_feed(self, name: str, url: str) -> None:
        """
        Add a new RSS feed.

        Args:
            name: Human-readable feed name.
            url: RSS feed URL.
        """
        self.feed_urls[name] = url
        logger.info(f"Added RSS feed: {name} ({url})")

    def remove_feed(self, name: str) -> bool:
        """
        Remove an RSS feed.

        Args:
            name: Feed name to remove.

        Returns:
            bool: True if feed was removed, False if not found.
        """
        if name in self.feed_urls:
            del self.feed_urls[name]
            logger.info(f"Removed RSS feed: {name}")
            return True
        return False
