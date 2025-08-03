"""
ArXiv API fetcher for AI/ML research papers.

This module implements fetching from the ArXiv API with strict adherence to
their rate limiting requirements (3-second delay between requests).
"""

import asyncio
import logging
from datetime import datetime, timedelta

import arxiv

from ..models.articles import Article, ArticleSource
from .base import BaseFetcher, FetchError

logger = logging.getLogger(__name__)


class ArxivFetcher(BaseFetcher):
    """
    Fetcher for ArXiv research papers in AI/ML categories.

    CRITICAL: ArXiv enforces a 3-second delay between requests.
    Using delay_seconds=3.0 in the client configuration is mandatory
    to avoid being banned.
    """

    def __init__(self) -> None:
        """Initialize ArXiv fetcher with proper rate limiting."""
        # CRITICAL: Use 3.0 second delay as required by ArXiv
        super().__init__(source=ArticleSource.ARXIV, rate_limit_delay=3.0)

        # Configure ArXiv client with rate limiting
        self.client = arxiv.Client(
            page_size=100,
            delay_seconds=3.0,  # CRITICAL: Respect ArXiv rate limit
            num_retries=5
        )

        # AI/ML categories to search
        self.categories = ["cs.AI", "cs.LG", "cs.CL"]

        logger.info(f"ArXiv fetcher initialized with {self.rate_limit_delay}s delay")

    async def fetch(self, max_articles: int = 100) -> list[Article]:
        """
        Fetch recent AI/ML papers from ArXiv.

        Args:
            max_articles: Maximum number of papers to fetch.

        Returns:
            List[Article]: List of fetched papers as Article objects.

        Raises:
            FetchError: If fetching fails.
        """
        try:
            logger.info(f"Fetching up to {max_articles} papers from ArXiv")

            # Build query for AI/ML categories
            # Using OR to get papers from any of the categories
            query = " OR ".join([f"cat:{cat}" for cat in self.categories])
            logger.debug(f"ArXiv query: {query}")

            search = arxiv.Search(
                query=query,
                max_results=max_articles,
                sort_by=arxiv.SortCriterion.SubmittedDate
            )

            articles = []

            # Note: arxiv.Client.results() is synchronous but handles rate limiting internally
            # We run it in a thread pool to avoid blocking the event loop
            results = await asyncio.get_event_loop().run_in_executor(
                None, lambda: list(self.client.results(search))
            )

            for result in results:
                try:
                    article = self._convert_arxiv_result_to_article(result)
                    articles.append(article)
                except Exception as e:
                    logger.warning(f"Failed to convert ArXiv result to article: {e}")
                    continue

            logger.info(f"Successfully fetched {len(articles)} papers from ArXiv")
            return articles

        except Exception as e:
            error_msg = f"Failed to fetch from ArXiv: {str(e)}"
            logger.error(error_msg)
            raise FetchError(error_msg, source=self.source)

    def _convert_arxiv_result_to_article(self, result: arxiv.Result) -> Article:
        """
        Convert ArXiv result to Article model.

        Args:
            result: ArXiv search result.

        Returns:
            Article: Converted article.
        """
        # Extract author names (limit to first 3 to avoid overly long strings)
        authors = [author.name for author in result.authors[:3]]
        author_str = ", ".join(authors)
        if len(result.authors) > 3:
            author_str += f" et al. ({len(result.authors)} authors)"

        # Use PDF URL if available, otherwise use entry ID
        url = result.pdf_url if result.pdf_url else result.entry_id

        # Clean up title and summary
        title = result.title.strip().replace('\n', ' ')
        content = result.summary.strip().replace('\n', ' ')

        # Extract ArXiv ID for source_id (format: "2301.00001v1" -> "2301.00001")
        source_id = result.entry_id.split('/')[-1].split('v')[0]

        return Article(
            source_id=source_id,
            source=ArticleSource.ARXIV,
            title=title,
            content=content,
            url=url,
            author=author_str if author_str else None,
            published_at=result.published,
            fetched_at=datetime.utcnow(),
            summary=None,
            relevance_score=None,
            embedding=None,
            is_duplicate=False,
            duplicate_of=None
        )

    async def fetch_recent(self, hours: int = 24) -> list[Article]:
        """
        Fetch papers published in the last N hours.

        Args:
            hours: Number of hours to look back.

        Returns:
            List[Article]: Recent papers.
        """
        cutoff_date = datetime.utcnow() - timedelta(hours=hours)

        # Fetch articles and filter by date
        articles = await self.fetch(max_articles=200)  # Fetch more to account for filtering

        recent_articles = [
            article for article in articles
            if article.published_at >= cutoff_date
        ]

        logger.info(f"Found {len(recent_articles)} papers from last {hours} hours")
        return recent_articles

    def get_supported_categories(self) -> list[str]:
        """
        Get list of supported ArXiv categories.

        Returns:
            List[str]: Supported category codes.
        """
        return self.categories.copy()
