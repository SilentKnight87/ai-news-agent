"""
PydanticAI agent for daily digest generation.

This module implements an AI agent that creates coherent daily summaries
from multiple articles, identifying key themes and notable developments.
"""

import logging
from datetime import datetime

from pydantic_ai import Agent

from ..config import get_settings
from ..models.articles import Article, DailyDigest
from ..models.schemas import DigestSummary
from .prompts import DIGEST_GENERATION_PROMPT

logger = logging.getLogger(__name__)


class DigestAgent:
    """
    PydanticAI-powered digest generator.
    
    Uses Google Gemini to analyze multiple articles and create
    coherent daily summaries with key themes and developments.
    """

    def __init__(self):
        """Initialize the digest agent."""
        import os
        self.settings = get_settings()

        # Set GOOGLE_API_KEY environment variable for PydanticAI
        os.environ['GOOGLE_API_KEY'] = self.settings.gemini_api_key

        # Initialize PydanticAI agent with Gemini
        self.agent = Agent(
            model='gemini-1.5-flash',
            output_type=DigestSummary,
            system_prompt=DIGEST_GENERATION_PROMPT,
        )

        logger.info("Digest agent initialized with Gemini")

    async def generate_digest(
        self,
        articles: list[Article],
        digest_date: datetime,
        max_summary_length: int = 2000
    ) -> DailyDigest:
        """
        Generate a daily digest from articles.
        
        Args:
            articles: List of articles to summarize.
            digest_date: Date for the digest.
            max_summary_length: Maximum length of summary text.
            
        Returns:
            DailyDigest: Generated digest with summary and metadata.
            
        Raises:
            Exception: If digest generation fails.
        """
        try:
            if not articles:
                raise ValueError("Cannot generate digest from empty article list")

            logger.info(f"Generating digest from {len(articles)} articles for {digest_date.date()}")

            # Prepare input for the agent
            input_text = self._prepare_digest_input(articles, max_summary_length)

            # Generate digest summary using AI
            result = await self.agent.run(input_text)
            digest_summary = result.data

            # Create DailyDigest object
            digest = DailyDigest(
                digest_date=digest_date,
                summary_text=digest_summary.summary_text,
                total_articles_processed=len(articles),
                top_articles=self._select_top_articles(articles),
                key_themes=digest_summary.key_themes,
                notable_developments=digest_summary.notable_developments
            )

            logger.info(f"Generated digest with {len(digest.key_themes)} themes")

            # Queue audio generation (non-blocking)
            try:
                from ..services.audio_queue import get_audio_queue
                audio_queue = get_audio_queue()

                # Note: digest.id needs to be set after saving to database
                # This will be done in the repository layer
                # For now, we'll add a flag to indicate audio should be generated
                digest._generate_audio = True

            except Exception as e:
                logger.warning(f"Could not queue audio generation: {e}")

            return digest

        except Exception as e:
            logger.error(f"Failed to generate digest: {e}")
            raise

    def _prepare_digest_input(
        self,
        articles: list[Article],
        max_length: int
    ) -> str:
        """
        Prepare input text for digest generation.
        
        Args:
            articles: Articles to include in digest.
            max_length: Maximum length for the summary.
            
        Returns:
            str: Formatted input for the AI agent.
        """
        # Sort articles by relevance score (highest first)
        sorted_articles = sorted(
            articles,
            key=lambda a: a.relevance_score or 0,
            reverse=True
        )

        # Create article summaries for the agent
        article_summaries = []
        for i, article in enumerate(sorted_articles[:20], 1):  # Limit to top 20
            summary = f"""
Article {i}:
Title: {article.title}
Source: {article.source.value}
Relevance: {article.relevance_score}/100
Published: {article.published_at.strftime('%Y-%m-%d %H:%M')}
Categories: {', '.join(article.categories or [])}
Summary: {article.summary or 'No summary available'}
Key Points: {'; '.join(article.key_points or [])}
"""
            article_summaries.append(summary.strip())

        input_text = f"""
Please generate a daily digest for {len(articles)} AI/ML articles.

Target Summary Length: {max_length} characters maximum
Date: {sorted_articles[0].published_at.strftime('%Y-%m-%d')}

Articles to summarize:
{'='*50}
{chr(10).join(article_summaries)}
{'='*50}

Please create a coherent daily summary that:
1. Identifies the main themes across all articles
2. Highlights the most significant developments
3. Provides context about trends and implications
4. Maintains the specified character limit
"""

        return input_text

    def _select_top_articles(
        self,
        articles: list[Article],
        max_count: int = 10
    ) -> list[Article]:
        """
        Select top articles for inclusion in digest.
        
        Args:
            articles: All articles to choose from.
            max_count: Maximum number of articles to include.
            
        Returns:
            List[Article]: Top articles sorted by relevance.
        """
        # Sort by relevance score and published date
        sorted_articles = sorted(
            articles,
            key=lambda a: (a.relevance_score or 0, a.published_at),
            reverse=True
        )

        return sorted_articles[:max_count]

    async def generate_quick_summary(
        self,
        articles: list[Article],
        max_length: int = 500
    ) -> str:
        """
        Generate a quick summary of articles without full digest structure.
        
        Args:
            articles: Articles to summarize.
            max_length: Maximum length of summary.
            
        Returns:
            str: Quick summary text.
        """
        try:
            if not articles:
                return "No articles available for summary."

            # Use a simpler agent for quick summaries
            quick_agent = Agent(
                model='gemini-1.5-flash',
                output_type=str,
                system_prompt=f"""You are a technical news summarizer. Create a concise summary 
                of AI/ML news articles in {max_length} characters or less. Focus on key developments 
                and trends. Be informative but brief."""
            )

            # Prepare simplified input
            titles_and_summaries = []
            for article in articles[:10]:  # Limit to top 10 for quick summary
                text = f"{article.title}"
                if article.summary:
                    text += f" - {article.summary[:100]}..."
                titles_and_summaries.append(text)

            input_text = f"""
Summarize these {len(articles)} AI/ML articles in {max_length} characters:

{chr(10).join(titles_and_summaries)}
"""

            result = await quick_agent.run(input_text)
            return result.data.strip()

        except Exception as e:
            logger.error(f"Failed to generate quick summary: {e}")
            return f"Summary generation failed for {len(articles)} articles."

    async def generate_themed_digest(
        self,
        articles: list[Article],
        theme: str,
        digest_date: datetime
    ) -> DailyDigest:
        """
        Generate a digest focused on a specific theme.
        
        Args:
            articles: Articles to analyze.
            theme: Specific theme to focus on (e.g., "LLMs", "Computer Vision").
            digest_date: Date for the digest.
            
        Returns:
            DailyDigest: Theme-focused digest.
        """
        try:
            # Filter articles that are relevant to the theme
            relevant_articles = []
            for article in articles:
                if self._is_article_relevant_to_theme(article, theme):
                    relevant_articles.append(article)

            if not relevant_articles:
                logger.warning(f"No articles found relevant to theme: {theme}")
                relevant_articles = articles[:5]  # Fallback to top articles

            logger.info(f"Generating themed digest for '{theme}' with {len(relevant_articles)} articles")

            # Modify the input to focus on the theme
            input_text = f"""
Generate a themed digest focusing specifically on: {theme}

Date: {digest_date.strftime('%Y-%m-%d')}
Theme Focus: {theme}
Articles Analyzed: {len(relevant_articles)}

{self._prepare_digest_input(relevant_articles, 2000)}

Please emphasize developments related to {theme} and how they connect to broader trends.
"""

            result = await self.agent.run(input_text)
            digest_summary = result.data

            # Create themed digest
            digest = DailyDigest(
                digest_date=digest_date,
                summary_text=f"[{theme} Focus] {digest_summary.summary_text}",
                total_articles_processed=len(relevant_articles),
                top_articles=self._select_top_articles(relevant_articles),
                key_themes=[theme] + digest_summary.key_themes,
                notable_developments=digest_summary.notable_developments
            )

            return digest

        except Exception as e:
            logger.error(f"Failed to generate themed digest for '{theme}': {e}")
            raise

    def _is_article_relevant_to_theme(self, article: Article, theme: str) -> bool:
        """
        Check if an article is relevant to a specific theme.
        
        Args:
            article: Article to check.
            theme: Theme to match against.
            
        Returns:
            bool: True if article is relevant to theme.
        """
        theme_lower = theme.lower()

        # Check title, categories, and key points
        text_to_check = [
            article.title.lower(),
            ' '.join(article.categories or []).lower(),
            ' '.join(article.key_points or []).lower()
        ]

        if article.summary:
            text_to_check.append(article.summary.lower())

        combined_text = ' '.join(text_to_check)

        # Simple keyword matching - could be enhanced with NLP
        theme_keywords = theme_lower.split()
        for keyword in theme_keywords:
            if keyword in combined_text:
                return True

        return False


# Global digest agent instance (lazy initialization)
_digest_agent = None


def get_digest_agent() -> DigestAgent:
    """Get the global digest agent instance (lazy initialization)."""
    global _digest_agent
    if _digest_agent is None:
        _digest_agent = DigestAgent()
    return _digest_agent
