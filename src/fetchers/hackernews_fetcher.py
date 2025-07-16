"""
HackerNews API fetcher for AI/ML related stories.

This module implements fetching from the HackerNews Firebase API and
filters for AI/ML related content based on keywords.
"""

import asyncio
import logging
import re
from datetime import datetime, timedelta

from ..models.articles import Article, ArticleSource
from .base import BaseFetcher, FetchError, RateLimitedHTTPClient

logger = logging.getLogger(__name__)


class HackerNewsFetcher(BaseFetcher):
    """
    Fetcher for HackerNews stories related to AI/ML.

    Uses the HackerNews Firebase API to fetch top stories and filters
    them for AI/ML relevance based on title and content keywords.
    """

    def __init__(self):
        """Initialize HackerNews fetcher with rate limiting."""
        # Respect unofficial 1 req/sec limit
        super().__init__(source=ArticleSource.HACKERNEWS, rate_limit_delay=1.0)

        self.base_url = "https://hacker-news.firebaseio.com/v0"
        self.http_client = RateLimitedHTTPClient(requests_per_second=1.0)

        # AI/ML keywords for filtering
        self.ai_keywords = {
            # Core AI/ML terms
            "ai", "artificial intelligence", "machine learning", "ml", "deep learning",
            "neural network", "neural", "nlp", "computer vision", "cv",

            # Specific technologies
            "gpt", "bert", "transformer", "llm", "large language model",
            "generative ai", "genai", "chatgpt", "claude", "gemini", "bard",
            "midjourney", "dall-e", "stable diffusion", "diffusion model",

            # Companies and products
            "openai", "anthropic", "google ai", "deepmind", "meta ai",
            "hugging face", "nvidia ai", "pytorch", "tensorflow", "keras",

            # Techniques and concepts
            "reinforcement learning", "rl", "supervised learning", "unsupervised learning",
            "training data", "model training", "fine-tuning", "prompt engineering",
            "attention mechanism", "backpropagation", "gradient descent",
            "convolutional", "recurrent", "lstm", "gru", "rnn", "cnn",

            # Applications
            "autonomous", "self-driving", "recommendation", "personalization",
            "fraud detection", "image recognition", "speech recognition",
            "language model", "text generation", "image generation",

            # Research and development
            "arxiv", "research paper", "algorithm", "dataset", "benchmark",
            "model architecture", "hyperparameter", "optimization"
        }

        logger.info("HackerNews fetcher initialized with AI/ML keyword filtering")

    async def fetch(self, max_articles: int = 100) -> list[Article]:
        """
        Fetch AI/ML related stories from HackerNews.

        Args:
            max_articles: Maximum number of stories to return.

        Returns:
            List[Article]: List of relevant HackerNews stories.

        Raises:
            FetchError: If fetching fails.
        """
        try:
            logger.info(f"Fetching HackerNews stories (max: {max_articles})")

            # Step 1: Get list of top story IDs
            story_ids = await self._fetch_top_story_ids()

            # Step 2: Fetch individual stories concurrently
            # Fetch more than needed to account for filtering
            fetch_count = min(max_articles * 3, len(story_ids))
            story_ids_to_fetch = story_ids[:fetch_count]

            logger.debug(f"Fetching {len(story_ids_to_fetch)} stories for filtering")

            stories = await self._fetch_stories_concurrent(story_ids_to_fetch)

            # Step 3: Filter for AI/ML relevance
            relevant_stories = self._filter_ai_ml_stories(stories)

            # Step 4: Convert to Article objects
            articles = []
            for story in relevant_stories[:max_articles]:
                try:
                    article = self._convert_story_to_article(story)
                    articles.append(article)
                except Exception as e:
                    logger.warning(f"Failed to convert story {story.get('id')}: {e}")
                    continue

            logger.info(f"Found {len(articles)} relevant AI/ML stories from HackerNews")
            return articles

        except Exception as e:
            error_msg = f"Failed to fetch from HackerNews: {str(e)}"
            logger.error(error_msg)
            raise FetchError(error_msg, source=self.source)

    async def _fetch_top_story_ids(self) -> list[int]:
        """Fetch list of top story IDs from HackerNews."""
        url = f"{self.base_url}/topstories.json"
        response = await self.http_client.get(url)
        story_ids = response.json()

        logger.debug(f"Fetched {len(story_ids)} top story IDs")
        return story_ids

    async def _fetch_stories_concurrent(self, story_ids: list[int]) -> list[dict]:
        """
        Fetch multiple stories concurrently with rate limiting.

        Args:
            story_ids: List of story IDs to fetch.

        Returns:
            List[Dict]: List of story data.
        """
        semaphore = asyncio.Semaphore(5)  # Limit concurrent requests

        async def fetch_single_story(story_id: int) -> dict | None:
            async with semaphore:
                try:
                    url = f"{self.base_url}/item/{story_id}.json"
                    response = await self.http_client.get(url)
                    return response.json()
                except Exception as e:
                    logger.warning(f"Failed to fetch story {story_id}: {e}")
                    return None

        # Create tasks for concurrent fetching
        tasks = [fetch_single_story(story_id) for story_id in story_ids]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out None results and exceptions
        stories = [
            result for result in results
            if result is not None and isinstance(result, dict)
        ]

        logger.debug(f"Successfully fetched {len(stories)}/{len(story_ids)} stories")
        return stories

    def _filter_ai_ml_stories(self, stories: list[dict]) -> list[dict]:
        """
        Filter stories for AI/ML relevance based on keywords.

        Args:
            stories: List of story data.

        Returns:
            List[Dict]: Filtered stories relevant to AI/ML.
        """
        relevant_stories = []

        for story in stories:
            # Skip deleted, dead, or non-story items
            if (story.get('deleted') or story.get('dead') or
                story.get('type') != 'story' or not story.get('title')):
                continue

            # Check if story is AI/ML relevant
            if self._is_ai_ml_relevant(story):
                relevant_stories.append(story)

        logger.debug(f"Filtered to {len(relevant_stories)} AI/ML relevant stories")
        return relevant_stories

    def _is_ai_ml_relevant(self, story: dict) -> bool:
        """
        Check if a story is relevant to AI/ML based on keywords.

        Args:
            story: Story data.

        Returns:
            bool: True if story is AI/ML relevant.
        """
        # Combine title and text for keyword matching
        text_to_check = ""

        if story.get('title'):
            text_to_check += story['title'].lower()

        if story.get('text'):
            text_to_check += " " + story['text'].lower()

        if story.get('url'):
            text_to_check += " " + story['url'].lower()

        # Check for keyword matches
        for keyword in self.ai_keywords:
            if keyword in text_to_check:
                logger.debug(f"Story {story.get('id')} matched keyword: {keyword}")
                return True

        return False

    def _convert_story_to_article(self, story: dict) -> Article:
        """
        Convert HackerNews story to Article model.

        Args:
            story: HackerNews story data.

        Returns:
            Article: Converted article.
        """
        # Extract basic information
        story_id = str(story['id'])
        title = story.get('title', '').strip()
        author = story.get('by', '')

        # Handle URL and content
        url = story.get('url')
        if not url:
            # If no URL, use HackerNews item page
            url = f"https://news.ycombinator.com/item?id={story_id}"

        # Use story text if available, otherwise use title as content
        content = story.get('text', '')
        if content:
            # Clean HTML from text
            content = re.sub(r'<[^>]+>', '', content)
            content = content.strip()
        else:
            content = title

        # Convert timestamp
        published_at = datetime.utcfromtimestamp(story.get('time', 0))

        return Article(
            source_id=story_id,
            source=ArticleSource.HACKERNEWS,
            title=title,
            content=content,
            url=url,
            author=author if author else None,
            published_at=published_at,
            fetched_at=datetime.utcnow()
        )

    async def fetch_recent(self, hours: int = 24) -> list[Article]:
        """
        Fetch recent AI/ML stories from the last N hours.

        Args:
            hours: Number of hours to look back.

        Returns:
            List[Article]: Recent relevant stories.
        """
        cutoff_date = datetime.utcnow() - timedelta(hours=hours)

        # Fetch more articles to account for time filtering
        articles = await self.fetch(max_articles=200)

        recent_articles = [
            article for article in articles
            if article.published_at >= cutoff_date
        ]

        logger.info(f"Found {len(recent_articles)} recent stories from last {hours} hours")
        return recent_articles

    def get_ai_keywords(self) -> set[str]:
        """
        Get the set of AI/ML keywords used for filtering.

        Returns:
            Set[str]: AI/ML keywords.
        """
        return self.ai_keywords.copy()
