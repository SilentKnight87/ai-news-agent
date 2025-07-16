"""
Deduplication service for identifying and handling duplicate articles.

This module implements semantic deduplication using vector embeddings
and URL matching to prevent duplicate stories from being stored.
"""

import logging
from datetime import datetime, timedelta
from uuid import UUID

from supabase import Client

from ..config import get_settings
from ..models.articles import Article, ArticleSimilarity
from .embeddings import get_embeddings_service

logger = logging.getLogger(__name__)


class DeduplicationService:
    """
    Service for detecting and handling duplicate articles.

    Uses both exact URL matching and semantic similarity via vector
    embeddings to identify duplicate content across different sources.
    """

    def __init__(self, supabase_client: Client):
        """
        Initialize deduplication service.

        Args:
            supabase_client: Supabase client for database operations.
        """
        self.supabase = supabase_client
        self.settings = get_settings()
        self.embeddings_service = get_embeddings_service()

        # Use threshold from settings
        self.similarity_threshold = self.settings.similarity_threshold

        logger.info(f"Deduplication service initialized (threshold: {self.similarity_threshold})")

    async def find_duplicates(
        self,
        article: Article,
        check_recent_hours: int = 48
    ) -> UUID | None:
        """
        Find if an article is a duplicate of existing content.

        Args:
            article: Article to check for duplicates.
            check_recent_hours: Only check articles from last N hours.

        Returns:
            UUID: ID of the original article if duplicate found, None otherwise.
        """
        try:
            # Step 1: Check for exact URL match first (fastest)
            url_duplicate = await self._find_url_duplicate(article)
            if url_duplicate:
                logger.debug(f"Found URL duplicate for: {article.url}")
                return url_duplicate

            # Step 2: Generate embedding if not already present
            if not article.embedding:
                article.embedding = await self.embeddings_service.generate_article_embedding(
                    article.title, article.content
                )

            # Step 3: Check for semantic similarity
            similarity_duplicate = await self._find_similarity_duplicate(
                article, check_recent_hours
            )
            if similarity_duplicate:
                logger.debug(f"Found similarity duplicate for: {article.title}")
                return similarity_duplicate

            logger.debug(f"No duplicates found for: {article.title}")
            return None

        except Exception as e:
            logger.error(f"Error checking duplicates for '{article.title}': {e}")
            # Return None to allow article to proceed if deduplication fails
            return None

    async def _find_url_duplicate(self, article: Article) -> UUID | None:
        """
        Find duplicate based on exact URL match.

        Args:
            article: Article to check.

        Returns:
            UUID: Original article ID if found, None otherwise.
        """
        try:
            response = self.supabase.table("articles").select("id").eq(
                "url", article.url
            ).eq(
                "is_duplicate", False
            ).limit(1).execute()

            if response.data:
                return UUID(response.data[0]["id"])

            return None

        except Exception as e:
            logger.error(f"Error checking URL duplicate: {e}")
            return None

    async def _find_similarity_duplicate(
        self,
        article: Article,
        check_recent_hours: int
    ) -> UUID | None:
        """
        Find duplicate based on vector similarity.

        Args:
            article: Article to check.
            check_recent_hours: Hours to look back.

        Returns:
            UUID: Original article ID if similar article found, None otherwise.
        """
        if not article.embedding:
            logger.warning("No embedding available for similarity check")
            return None

        try:
            # Calculate cutoff date
            cutoff_date = datetime.utcnow() - timedelta(hours=check_recent_hours)

            # Use Supabase RPC function for vector similarity search
            response = self.supabase.rpc(
                "match_articles",
                {
                    "query_embedding": article.embedding,
                    "match_threshold": self.similarity_threshold,
                    "match_count": 5
                }
            ).execute()

            if not response.data:
                return None

            # Check each match for additional criteria
            for match in response.data:
                match_date = datetime.fromisoformat(
                    match["published_at"].replace("Z", "+00:00")
                )

                # Only consider recent articles
                if match_date < cutoff_date:
                    continue

                # Check if similarity is above threshold and criteria match
                if self._is_likely_duplicate(article, match):
                    return UUID(match["id"])

            return None

        except Exception as e:
            logger.error(f"Error in similarity search: {e}")
            return None

    def _is_likely_duplicate(self, article: Article, match: dict) -> bool:
        """
        Determine if a similarity match is likely a duplicate.

        Args:
            article: Original article.
            match: Similarity match result.

        Returns:
            bool: True if likely duplicate.
        """
        similarity_score = match["similarity"]

        # High similarity threshold
        if similarity_score > 0.95:
            return True

        # Medium similarity with additional checks
        if similarity_score > self.similarity_threshold:
            # Check if published on same day
            article_date = article.published_at.date()
            match_date = datetime.fromisoformat(
                match["published_at"].replace("Z", "+00:00")
            ).date()

            if article_date == match_date:
                return True

            # Check for very similar titles
            title_similarity = self._calculate_title_similarity(
                article.title, match["title"]
            )

            if title_similarity > 0.8:
                return True

        return False

    def _calculate_title_similarity(self, title1: str, title2: str) -> float:
        """
        Calculate similarity between two titles using simple token overlap.

        Args:
            title1: First title.
            title2: Second title.

        Returns:
            float: Similarity score (0-1).
        """
        # Simple token-based similarity
        tokens1 = set(title1.lower().split())
        tokens2 = set(title2.lower().split())

        # Remove common stop words
        stop_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by"}
        tokens1 = tokens1 - stop_words
        tokens2 = tokens2 - stop_words

        if not tokens1 or not tokens2:
            return 0.0

        intersection = tokens1.intersection(tokens2)
        union = tokens1.union(tokens2)

        return len(intersection) / len(union)

    async def mark_as_duplicate(
        self,
        article: Article,
        original_id: UUID
    ) -> None:
        """
        Mark an article as a duplicate in the database.

        Args:
            article: Article to mark as duplicate.
            original_id: ID of the original article.
        """
        try:
            if article.id:
                # Update existing article
                self.supabase.table("articles").update({
                    "is_duplicate": True,
                    "duplicate_of": str(original_id)
                }).eq("id", str(article.id)).execute()

            logger.debug(f"Marked article as duplicate of {original_id}")

        except Exception as e:
            logger.error(f"Error marking article as duplicate: {e}")

    async def get_similar_articles(
        self,
        article: Article,
        limit: int = 10
    ) -> list[ArticleSimilarity]:
        """
        Get articles similar to the given article.

        Args:
            article: Article to find similar articles for.
            limit: Maximum number of similar articles to return.

        Returns:
            List[ArticleSimilarity]: List of similar articles with scores.
        """
        if not article.embedding:
            # Generate embedding if not present
            article.embedding = await self.embeddings_service.generate_article_embedding(
                article.title, article.content
            )

        try:
            response = self.supabase.rpc(
                "match_articles",
                {
                    "query_embedding": article.embedding,
                    "match_threshold": 0.3,  # Lower threshold for exploration
                    "match_count": limit
                }
            ).execute()

            similar_articles = []

            for match in response.data:
                # Fetch full article data
                article_response = self.supabase.table("articles").select("*").eq(
                    "id", match["id"]
                ).single().execute()

                if article_response.data:
                    # Convert database record to Article model
                    from ..models.database import article_db_to_pydantic
                    similar_article = article_db_to_pydantic(article_response.data)

                    similarity = ArticleSimilarity(
                        article=similar_article,
                        similarity_score=match["similarity"]
                    )
                    similar_articles.append(similarity)

            return similar_articles

        except Exception as e:
            logger.error(f"Error finding similar articles: {e}")
            return []

    async def process_articles_for_duplicates(
        self,
        articles: list[Article]
    ) -> tuple[list[Article], list[Article]]:
        """
        Process a list of articles to identify and separate duplicates.

        Args:
            articles: List of articles to process.

        Returns:
            Tuple[List[Article], List[Article]]: (unique_articles, duplicate_articles)
        """
        if not articles:
            return [], []

        logger.info(f"Processing {len(articles)} articles for duplicates")

        unique_articles = []
        duplicate_articles = []

        for article in articles:
            try:
                # Check if this article is a duplicate
                original_id = await self.find_duplicates(article)

                if original_id:
                    # Mark as duplicate
                    article.is_duplicate = True
                    article.duplicate_of = original_id
                    duplicate_articles.append(article)

                    logger.debug(f"Identified duplicate: {article.title}")
                else:
                    # Unique article
                    unique_articles.append(article)

            except Exception as e:
                logger.warning(f"Error processing article for duplicates: {e}")
                # Include in unique articles if processing fails
                unique_articles.append(article)

        logger.info(
            f"Deduplication complete: {len(unique_articles)} unique, "
            f"{len(duplicate_articles)} duplicates"
        )

        return unique_articles, duplicate_articles

    def get_deduplication_stats(self) -> dict:
        """
        Get statistics about deduplication performance.

        Returns:
            dict: Deduplication statistics.
        """
        try:
            # Get counts from database
            total_response = self.supabase.table("articles").select(
                "id", count="exact"
            ).execute()

            duplicates_response = self.supabase.table("articles").select(
                "id", count="exact"
            ).eq("is_duplicate", True).execute()

            total_articles = total_response.count or 0
            duplicate_articles = duplicates_response.count or 0
            unique_articles = total_articles - duplicate_articles

            duplicate_rate = (duplicate_articles / total_articles * 100) if total_articles > 0 else 0

            return {
                "total_articles": total_articles,
                "unique_articles": unique_articles,
                "duplicate_articles": duplicate_articles,
                "duplicate_rate_percent": round(duplicate_rate, 2),
                "similarity_threshold": self.similarity_threshold
            }

        except Exception as e:
            logger.error(f"Error getting deduplication stats: {e}")
            return {
                "error": "Failed to retrieve statistics",
                "similarity_threshold": self.similarity_threshold
            }
