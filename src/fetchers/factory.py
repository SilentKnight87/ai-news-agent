"""
Fetcher factory for managing news source fetchers.

This module provides a centralized way to create and manage fetchers
for different news sources.
"""

import logging

from ..models.articles import ArticleSource
from .arxiv_fetcher import ArxivFetcher
from .base import BaseFetcher
from .hackernews_fetcher import HackerNewsFetcher
from .rss_fetcher import RSSFetcher

logger = logging.getLogger(__name__)


class FetcherFactory:
    """
    Factory for creating and managing news fetchers.

    Provides a centralized way to instantiate fetchers for different
    news sources and coordinate fetching operations.
    """

    def __init__(self):
        """Initialize the fetcher factory."""
        self._fetcher_classes: dict[ArticleSource, type[BaseFetcher]] = {
            ArticleSource.ARXIV: ArxivFetcher,
            ArticleSource.HACKERNEWS: HackerNewsFetcher,
            ArticleSource.RSS: RSSFetcher,
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
            self._fetcher_instances[source] = fetcher_class()
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

    def get_health_status(self) -> dict[str, any]:
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


# Global factory instance
fetcher_factory = FetcherFactory()
