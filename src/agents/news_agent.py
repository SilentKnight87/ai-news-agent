"""
PydanticAI agent for news article analysis.

This module implements the core AI agent that analyzes news articles
for relevance and extracts structured information using PydanticAI.
"""

import asyncio
import logging

from pydantic_ai import Agent

from ..config import get_settings
from ..models.articles import Article
from ..models.schemas import NewsAnalysis
from .prompts import NEWS_ANALYSIS_PROMPT

logger = logging.getLogger(__name__)


class NewsAnalyzer:
    """
    PydanticAI-powered news analyzer.

    Uses Google Gemini to analyze articles for AI/ML relevance and
    extract structured information including summaries, key points,
    and relevance scores.
    """

    def __init__(self):
        """Initialize the news analyzer agent."""
        import os
        self.settings = get_settings()

        # Set GOOGLE_API_KEY environment variable for PydanticAI
        os.environ['GOOGLE_API_KEY'] = self.settings.gemini_api_key

        # Initialize PydanticAI agent with Gemini
        self.agent = Agent(
            model='gemini-1.5-flash',
            output_type=NewsAnalysis,
            system_prompt=NEWS_ANALYSIS_PROMPT,
        )

        logger.info("News analyzer agent initialized with Gemini")

    async def analyze_article(self, article: Article) -> NewsAnalysis:
        """
        Analyze a single article for AI/ML relevance and key information.

        Args:
            article: Article to analyze.

        Returns:
            NewsAnalysis: Structured analysis result.

        Raises:
            Exception: If analysis fails.
        """
        try:
            # Prepare input text for the agent
            input_text = self._prepare_input_text(article)

            logger.debug(f"Analyzing article: {article.title[:50]}...")

            # Run the agent
            result = await self.agent.run(input_text)

            logger.debug(f"Analysis complete. Relevance score: {result.data.relevance_score}")

            return result.data

        except Exception as e:
            logger.error(f"Failed to analyze article '{article.title}': {e}")
            raise

    async def analyze_articles_batch(
        self,
        articles: list[Article],
        max_concurrent: int = 5
    ) -> list[NewsAnalysis | None]:
        """
        Analyze multiple articles concurrently with rate limiting.

        Args:
            articles: List of articles to analyze.
            max_concurrent: Maximum concurrent analyses.

        Returns:
            List[Optional[NewsAnalysis]]: Analysis results (None for failed analyses).
        """
        if not articles:
            return []

        logger.info(f"Analyzing {len(articles)} articles with concurrency {max_concurrent}")

        semaphore = asyncio.Semaphore(max_concurrent)

        async def analyze_with_semaphore(article: Article) -> NewsAnalysis | None:
            async with semaphore:
                try:
                    return await self.analyze_article(article)
                except Exception as e:
                    logger.warning(f"Failed to analyze article '{article.title}': {e}")
                    return None

        # Create tasks for concurrent execution
        tasks = [analyze_with_semaphore(article) for article in articles]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Convert exceptions to None
        final_results = []
        for result in results:
            if isinstance(result, Exception):
                final_results.append(None)
            else:
                final_results.append(result)

        successful_analyses = sum(1 for r in final_results if r is not None)
        logger.info(f"Successfully analyzed {successful_analyses}/{len(articles)} articles")

        return final_results

    def _prepare_input_text(self, article: Article) -> str:
        """
        Prepare input text for the AI agent.

        Args:
            article: Article to prepare.

        Returns:
            str: Formatted input text.
        """
        # Include source information for context
        source_info = f"Source: {article.source.value}"
        if article.author:
            source_info += f" | Author: {article.author}"

        # Truncate content if too long to stay within token limits
        content = article.content
        if len(content) > 4000:  # Conservative limit
            content = content[:4000] + "... [truncated]"

        input_text = f"""{source_info}

Title: {article.title}

Content: {content}
"""

        return input_text

    async def quick_relevance_check(self, title: str, content: str) -> bool:
        """
        Quick relevance check for filtering before full analysis.

        Args:
            title: Article title.
            content: Article content (first few paragraphs).

        Returns:
            bool: True if article appears relevant to AI/ML.
        """
        try:
            # Ensure environment variable is set
            import os
            from ..config import get_settings
            settings = get_settings()
            os.environ['GOOGLE_API_KEY'] = settings.gemini_api_key

            # Use a simpler agent for quick filtering
            filter_agent = Agent(
                model='gemini-1.5-flash',
                output_type=str,
                system_prompt="""You are a content filter. Respond with only "RELEVANT" or "NOT_RELEVANT"
                                based on whether the content is about AI, ML, or related technologies."""
            )

            # Truncate content for quick check
            check_content = content[:1000] if len(content) > 1000 else content
            input_text = f"Title: {title}\n\nContent: {check_content}"

            result = await filter_agent.run(input_text)

            return result.data.strip().upper() == "RELEVANT"

        except Exception as e:
            logger.warning(f"Quick relevance check failed: {e}")
            # If check fails, assume relevant to be safe
            return True

    def update_article_with_analysis(self, article: Article, analysis: NewsAnalysis) -> Article:
        """
        Update article with analysis results.

        Args:
            article: Original article.
            analysis: Analysis results.

        Returns:
            Article: Updated article with analysis data.
        """
        # Create a copy of the article with analysis data
        updated_article = article.model_copy()
        updated_article.summary = analysis.summary
        updated_article.relevance_score = analysis.relevance_score
        updated_article.categories = analysis.categories
        updated_article.key_points = analysis.key_points

        return updated_article

    async def analyze_and_update_articles(
        self,
        articles: list[Article],
        min_relevance_score: float = 50.0
    ) -> list[Article]:
        """
        Analyze articles and return only those meeting relevance threshold.

        Args:
            articles: Articles to analyze.
            min_relevance_score: Minimum relevance score to include.

        Returns:
            List[Article]: Analyzed articles meeting relevance threshold.
        """
        if not articles:
            return []

        logger.info(f"Analyzing and filtering {len(articles)} articles")

        # Analyze all articles
        analyses = await self.analyze_articles_batch(articles)

        # Update articles with analysis and filter by relevance
        relevant_articles = []
        for article, analysis in zip(articles, analyses, strict=False):
            if analysis is None:
                continue

            if analysis.relevance_score >= min_relevance_score:
                updated_article = self.update_article_with_analysis(article, analysis)
                relevant_articles.append(updated_article)
            else:
                logger.debug(
                    f"Filtered out article '{article.title}' "
                    f"(relevance: {analysis.relevance_score})"
                )

        logger.info(
            f"Filtered to {len(relevant_articles)} relevant articles "
            f"(threshold: {min_relevance_score})"
        )

        return relevant_articles


# Global analyzer instance (lazy initialization)
_news_analyzer = None

def get_news_analyzer() -> NewsAnalyzer:
    """Get the global news analyzer instance (lazy initialization)."""
    global _news_analyzer
    if _news_analyzer is None:
        _news_analyzer = NewsAnalyzer()
    return _news_analyzer
