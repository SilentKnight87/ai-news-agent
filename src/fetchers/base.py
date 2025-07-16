"""
Base fetcher interface and common functionality.

This module defines the abstract base class that all news fetchers must implement,
along with common utilities like rate limiting and error handling.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timedelta

from ..models.articles import Article, ArticleSource, FetchResult

logger = logging.getLogger(__name__)


class BaseFetcher(ABC):
    """
    Abstract base class for all news fetchers.

    Defines the interface that all fetchers must implement and provides
    common functionality for rate limiting and error handling.
    """

    def __init__(self, source: ArticleSource, rate_limit_delay: float = 1.0):
        """
        Initialize the base fetcher.

        Args:
            source: The news source this fetcher handles.
            rate_limit_delay: Minimum delay between requests in seconds.
        """
        self.source = source
        self.rate_limit_delay = rate_limit_delay
        self._last_request_time: datetime | None = None
        self._error_count = 0
        self._circuit_breaker_open_until: datetime | None = None

    @abstractmethod
    async def fetch(self, max_articles: int = 100) -> list[Article]:
        """
        Fetch articles from the news source.

        Args:
            max_articles: Maximum number of articles to fetch.

        Returns:
            List[Article]: List of fetched articles.

        Raises:
            FetchError: If fetching fails.
        """
        pass

    async def fetch_with_result(self, max_articles: int = 100) -> FetchResult:
        """
        Fetch articles and return detailed result information.

        Args:
            max_articles: Maximum number of articles to fetch.

        Returns:
            FetchResult: Detailed fetch operation result.
        """
        start_time = datetime.utcnow()
        errors = []
        articles = []

        try:
            # Check circuit breaker
            if self._is_circuit_breaker_open():
                raise FetchError(f"Circuit breaker open for {self.source}")

            # Apply rate limiting
            await self._apply_rate_limit()

            # Fetch articles
            articles = await self.fetch(max_articles)

            # Reset error count on success
            self._error_count = 0

        except Exception as e:
            error_msg = f"Failed to fetch from {self.source}: {str(e)}"
            logger.error(error_msg)
            errors.append(error_msg)

            # Increment error count and potentially open circuit breaker
            self._error_count += 1
            if self._error_count >= 5:
                self._circuit_breaker_open_until = datetime.utcnow() + timedelta(minutes=5)
                logger.warning(f"Circuit breaker opened for {self.source}")

        duration = (datetime.utcnow() - start_time).total_seconds()

        return FetchResult(
            source=self.source,
            articles_fetched=len(articles),
            articles_new=len(articles),  # Will be updated by deduplication service
            articles_duplicates=0,      # Will be updated by deduplication service
            errors=errors,
            fetch_duration_seconds=duration,
            success=len(errors) == 0
        )

    async def _apply_rate_limit(self) -> None:
        """Apply rate limiting between requests."""
        if self._last_request_time is not None:
            time_since_last = (datetime.utcnow() - self._last_request_time).total_seconds()
            if time_since_last < self.rate_limit_delay:
                sleep_time = self.rate_limit_delay - time_since_last
                logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f}s")
                await asyncio.sleep(sleep_time)

        self._last_request_time = datetime.utcnow()

    def _is_circuit_breaker_open(self) -> bool:
        """Check if circuit breaker is currently open."""
        if self._circuit_breaker_open_until is None:
            return False

        if datetime.utcnow() >= self._circuit_breaker_open_until:
            # Circuit breaker timeout expired, reset
            self._circuit_breaker_open_until = None
            self._error_count = 0
            logger.info(f"Circuit breaker closed for {self.source}")
            return False

        return True

    def get_health_status(self) -> dict[str, any]:
        """
        Get health status information for this fetcher.

        Returns:
            Dict with health status information.
        """
        return {
            "source": self.source.value,
            "last_request_time": self._last_request_time.isoformat() if self._last_request_time else None,
            "error_count": self._error_count,
            "circuit_breaker_open": self._is_circuit_breaker_open(),
            "circuit_breaker_open_until": (
                self._circuit_breaker_open_until.isoformat()
                if self._circuit_breaker_open_until else None
            ),
        }


class FetchError(Exception):
    """Exception raised when fetching fails."""

    def __init__(self, message: str, source: ArticleSource | None = None):
        """
        Initialize fetch error.

        Args:
            message: Error message.
            source: Source that failed (if known).
        """
        super().__init__(message)
        self.source = source


class RateLimitedHTTPClient:
    """
    HTTP client with built-in rate limiting and retry logic.

    Provides a consistent interface for making HTTP requests with
    exponential backoff and jitter.
    """

    def __init__(self, requests_per_second: float = 1.0, max_retries: int = 3):
        """
        Initialize rate-limited HTTP client.

        Args:
            requests_per_second: Maximum requests per second.
            max_retries: Maximum number of retry attempts.
        """
        self.delay = 1.0 / requests_per_second
        self.max_retries = max_retries
        self._last_request_time: datetime | None = None

    async def get(self, url: str, **kwargs) -> any:
        """
        Make a rate-limited GET request with retries.

        Args:
            url: URL to request.
            **kwargs: Additional arguments for httpx.AsyncClient.get.

        Returns:
            Response object.

        Raises:
            FetchError: If request fails after all retries.
        """
        import random

        import httpx

        for attempt in range(self.max_retries + 1):
            try:
                # Apply rate limiting
                await self._apply_rate_limit()

                async with httpx.AsyncClient() as client:
                    response = await client.get(url, **kwargs)
                    response.raise_for_status()
                    return response

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:  # Rate limit
                    # Exponential backoff with jitter
                    delay = (2 ** attempt) + random.uniform(0.1, 0.3)
                    logger.warning(f"Rate limited, retrying in {delay:.2f}s")
                    await asyncio.sleep(delay)
                    continue
                else:
                    raise FetchError(f"HTTP error {e.response.status_code}: {e}")
            except Exception as e:
                if attempt == self.max_retries:
                    raise FetchError(f"Request failed after {self.max_retries} retries: {e}")

                # Exponential backoff
                delay = (2 ** attempt) + random.uniform(0.1, 0.3)
                logger.warning(f"Request failed (attempt {attempt + 1}), retrying in {delay:.2f}s")
                await asyncio.sleep(delay)

    async def _apply_rate_limit(self) -> None:
        """Apply rate limiting between requests."""
        if self._last_request_time is not None:
            time_since_last = (datetime.utcnow() - self._last_request_time).total_seconds()
            if time_since_last < self.delay:
                sleep_time = self.delay - time_since_last
                await asyncio.sleep(sleep_time)

        self._last_request_time = datetime.utcnow()
