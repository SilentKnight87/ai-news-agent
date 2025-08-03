"""
Fetcher factory for managing news source fetchers.

This module provides a centralized way to create and manage fetchers
for different news sources.
"""

import logging
from typing import Any

from ..models.articles import ArticleSource
from .arxiv_fetcher import ArxivFetcher
from .base import BaseFetcher
from .github_fetcher import GitHubFetcher
from .hackernews_fetcher import HackerNewsFetcher
from .huggingface_fetcher import HuggingFaceFetcher
from .reddit_fetcher import RedditFetcher
from .rss_fetcher import RSSFetcher

logger = logging.getLogger(__name__)


class FetcherFactory:
    """
    Factory for creating and managing news fetchers.

    Provides a centralized way to instantiate fetchers for different
    news sources and coordinate fetching operations.
    """

    def __init__(self, settings: Any = None):
        """
        Initialize the fetcher factory.
        
        Args:
            settings: Application settings for configuring fetchers.
        """
        self.settings = settings
        self._fetcher_classes: dict[ArticleSource, type[BaseFetcher]] = {
            ArticleSource.ARXIV: ArxivFetcher,
            ArticleSource.HACKERNEWS: HackerNewsFetcher,
            ArticleSource.RSS: RSSFetcher,
            ArticleSource.YOUTUBE: RSSFetcher,  # YouTube uses RSS fetcher
            ArticleSource.HUGGINGFACE: HuggingFaceFetcher,
            ArticleSource.REDDIT: RedditFetcher,
            ArticleSource.GITHUB: GitHubFetcher,
        }

        self._fetcher_instances: dict[ArticleSource, BaseFetcher] = {}

        logger.info("Fetcher factory initialized")

    def get_fetcher(self, source: ArticleSource) -> BaseFetcher:
        """
        Get a fetcher instance for the specified source.

        Args:
            source: The news source to get a fetcher for.

        Returns:
            BaseFetcher: Fetcher instance for the source.

        Raises:
            ValueError: If the source is not supported.
        """
        if source not in self._fetcher_classes:
            raise ValueError(f"Unsupported news source: {source}")

        # Use singleton pattern - create instance if it doesn't exist
        if source not in self._fetcher_instances:
            fetcher_class = self._fetcher_classes[source]
            self._fetcher_instances[source] = self._create_fetcher_instance(source, fetcher_class)
            logger.debug(f"Created fetcher instance for {source}")

        return self._fetcher_instances[source]

    def get_all_fetchers(self) -> dict[ArticleSource, BaseFetcher]:
        """
        Get all available fetcher instances.

        Returns:
            Dict[ArticleSource, BaseFetcher]: Mapping of sources to fetchers.
        """
        fetchers = {}
        for source in self._fetcher_classes:
            fetchers[source] = self.get_fetcher(source)
        return fetchers

    def get_supported_sources(self) -> list[ArticleSource]:
        """
        Get list of supported news sources.

        Returns:
            List[ArticleSource]: List of supported sources.
        """
        return list(self._fetcher_classes.keys())

    def is_source_supported(self, source: ArticleSource) -> bool:
        """
        Check if a news source is supported.

        Args:
            source: Source to check.

        Returns:
            bool: True if source is supported.
        """
        return source in self._fetcher_classes

    def get_health_status(self) -> dict[str, Any]:
        """
        Get health status for all fetchers.

        Returns:
            Dict: Health status information for all fetchers.
        """
        status = {
            "supported_sources": [source.value for source in self._fetcher_classes],
            "active_instances": [source.value for source in self._fetcher_instances],
            "fetcher_status": {}
        }

        # Get status from active fetcher instances
        for source, fetcher in self._fetcher_instances.items():
            status["fetcher_status"][source.value] = fetcher.get_health_status()

        return status

    def _create_fetcher_instance(self, source: ArticleSource, fetcher_class: type[BaseFetcher]) -> BaseFetcher:
        """
        Create a fetcher instance with appropriate configuration.
        
        Args:
            source: The article source type.
            fetcher_class: The fetcher class to instantiate.
            
        Returns:
            BaseFetcher: Configured fetcher instance.
        """
        # Create fetcher instances with required parameters
        if source in [ArticleSource.ARXIV, ArticleSource.HACKERNEWS]:
            # These fetchers don't need additional parameters
            return fetcher_class()

        elif source in [ArticleSource.RSS, ArticleSource.YOUTUBE]:
            # RSS fetcher (handles both RSS and YouTube)
            return fetcher_class()

        elif source == ArticleSource.HUGGINGFACE:
            # HuggingFace fetcher with optional API key
            hf_api_key = getattr(self.settings, 'hf_api_key', None) if self.settings else None
            return fetcher_class(hf_api_key=hf_api_key)

        elif source == ArticleSource.REDDIT:
            # Reddit fetcher with required credentials
            if not self.settings:
                raise ValueError("Settings required for Reddit fetcher")
            return fetcher_class(
                client_id=getattr(self.settings, 'reddit_client_id', ''),
                client_secret=getattr(self.settings, 'reddit_client_secret', ''),
                user_agent=getattr(self.settings, 'reddit_user_agent', 'AI-News-Aggregator/1.0'),
                username=getattr(self.settings, 'reddit_username', None)
            )

        elif source == ArticleSource.GITHUB:
            # GitHub fetcher with optional token
            github_token = getattr(self.settings, 'github_token', None) if self.settings else None
            return fetcher_class(github_token=github_token)

        else:
            # Fallback for unknown sources
            return fetcher_class()


# Global factory instance
fetcher_factory = FetcherFactory()
