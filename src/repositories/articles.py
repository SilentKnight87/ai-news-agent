"""
Article repository for database operations.

This module provides a data access layer for article operations
including CRUD operations, vector similarity search, and batch processing.
"""

import json
import logging
from datetime import datetime, timedelta
from uuid import UUID

from supabase import Client

from ..models.articles import Article, ArticleSource

logger = logging.getLogger(__name__)


class ArticleRepository:
    """
    Repository for article database operations.

    Provides a clean interface for all article-related database operations
    including creation, retrieval, updates, and vector similarity searches.
    """

    # Temporary mapping for new source types until database schema is updated
    _SOURCE_MAPPING = {
        ArticleSource.YOUTUBE: ArticleSource.RSS,
        ArticleSource.HUGGINGFACE: ArticleSource.RSS, 
        ArticleSource.REDDIT: ArticleSource.RSS,
        ArticleSource.GITHUB: ArticleSource.RSS
    }

    def __init__(self, supabase_client: Client):
        """
        Initialize the article repository.

        Args:
            supabase_client: Supabase client for database operations.
        """
        self.supabase = supabase_client
        logger.info("Article repository initialized")

    async def create_article(self, article: Article) -> Article:
        """
        Create a new article in the database.

        Args:
            article: Article to create.

        Returns:
            Article: Created article with assigned ID.

        Raises:
            Exception: If creation fails.
        """
        try:
            # Prepare article data for insertion
            article_data = self._article_to_db_dict(article)

            # Insert into database
            response = self.supabase.table("articles").insert(article_data).execute()

            if not response.data:
                raise Exception("Failed to create article - no data returned")

            # Convert back to Article model
            created_article = self._db_dict_to_article(response.data[0])

            logger.debug(f"Created article: {created_article.title}")
            return created_article

        except Exception as e:
            logger.error(f"Failed to create article '{article.title}': {e}")
            raise

    async def get_article_by_id(self, article_id: UUID) -> Article | None:
        """
        Get an article by its ID.

        Args:
            article_id: Article ID to retrieve.

        Returns:
            Article: Article if found, None otherwise.
        """
        try:
            response = self.supabase.table("articles").select("*").eq(
                "id", str(article_id)
            ).single().execute()

            if response.data:
                return self._db_dict_to_article(response.data)

            return None

        except Exception as e:
            logger.error(f"Failed to get article {article_id}: {e}")
            return None

    async def get_articles(
        self,
        limit: int = 50,
        offset: int = 0,
        source: ArticleSource | None = None,
        min_relevance_score: float | None = None,
        since: datetime | None = None,
        include_duplicates: bool = False
    ) -> list[Article]:
        """
        Get articles with filtering and pagination.

        Args:
            limit: Maximum number of articles to return.
            offset: Number of articles to skip.
            source: Filter by specific source.
            min_relevance_score: Minimum relevance score filter.
            since: Only return articles published after this date.
            include_duplicates: Whether to include duplicate articles.

        Returns:
            List[Article]: List of matching articles.
        """
        try:
            query = self.supabase.table("articles").select("*")

            # Apply filters
            if not include_duplicates:
                query = query.eq("is_duplicate", False)

            if source:
                query = query.eq("source", source.value)

            if min_relevance_score is not None:
                query = query.gte("relevance_score", min_relevance_score)

            if since:
                query = query.gte("published_at", since.isoformat())

            # Apply pagination and ordering
            query = query.order("published_at", desc=True)
            query = query.range(offset, offset + limit - 1)

            response = query.execute()

            articles = []
            for article_data in response.data:
                article = self._db_dict_to_article(article_data)
                articles.append(article)

            logger.debug(f"Retrieved {len(articles)} articles")
            return articles

        except Exception as e:
            logger.error(f"Failed to get articles: {e}")
            return []

    async def update_article(self, article_id: UUID, updates: dict) -> Article | None:
        """
        Update an article with new data.

        Args:
            article_id: ID of article to update.
            updates: Dictionary of fields to update.

        Returns:
            Article: Updated article if successful, None otherwise.
        """
        try:
            # Convert embedding list to JSON string if present
            if 'embedding' in updates and updates['embedding']:
                updates['embedding'] = json.dumps(updates['embedding'])

            response = self.supabase.table("articles").update(updates).eq(
                "id", str(article_id)
            ).execute()

            if response.data:
                return self._db_dict_to_article(response.data[0])

            return None

        except Exception as e:
            logger.error(f"Failed to update article {article_id}: {e}")
            return None

    async def update_article_analysis(
        self,
        article_id: UUID,
        summary: str,
        relevance_score: float,
        categories: list[str],
        key_points: list[str],
        embedding: list[float] | None = None
    ) -> Article | None:
        """
        Update an article with AI analysis results.

        Args:
            article_id: Article ID to update.
            summary: AI-generated summary.
            relevance_score: Relevance score (0-100).
            categories: List of categories.
            key_points: List of key points.
            embedding: Optional embedding vector.

        Returns:
            Article: Updated article if successful, None otherwise.
        """
        updates = {
            "summary": summary,
            "relevance_score": relevance_score,
            "categories": categories,
            "key_points": key_points
        }

        if embedding:
            updates["embedding"] = embedding

        return await self.update_article(article_id, updates)

    async def delete_article(self, article_id: UUID) -> bool:
        """
        Delete an article from the database.

        Args:
            article_id: ID of article to delete.

        Returns:
            bool: True if deletion successful, False otherwise.
        """
        try:
            response = self.supabase.table("articles").delete().eq(
                "id", str(article_id)
            ).execute()

            return len(response.data) > 0

        except Exception as e:
            logger.error(f"Failed to delete article {article_id}: {e}")
            return False

    async def batch_create_articles(self, articles: list[Article]) -> list[Article]:
        """
        Create multiple articles in a single batch operation.

        Args:
            articles: List of articles to create.

        Returns:
            List[Article]: List of created articles.
        """
        if not articles:
            return []

        try:
            # Prepare batch data
            batch_data = []
            for article in articles:
                article_data = self._article_to_db_dict(article)
                batch_data.append(article_data)

            # Batch insert
            response = self.supabase.table("articles").insert(batch_data).execute()

            # Convert response back to Article models
            created_articles = []
            for article_data in response.data:
                article = self._db_dict_to_article(article_data)
                created_articles.append(article)

            logger.info(f"Batch created {len(created_articles)} articles")
            return created_articles

        except Exception as e:
            logger.error(f"Failed to batch create articles: {e}")
            return []

    async def find_by_source_id(
        self,
        source: ArticleSource,
        source_id: str
    ) -> Article | None:
        """
        Find an article by source and source ID.

        Args:
            source: Article source.
            source_id: Source-specific article ID.

        Returns:
            Article: Article if found, None otherwise.
        """
        try:
            response = self.supabase.table("articles").select("*").eq(
                "source", source.value
            ).eq(
                "source_id", source_id
            ).single().execute()

            if response.data:
                return self._db_dict_to_article(response.data)

            return None

        except Exception:
            logger.debug(f"Article not found for {source.value}:{source_id}")
            return None

    async def similarity_search(
        self,
        embedding: list[float],
        threshold: float = 0.8,
        limit: int = 10,
        exclude_duplicates: bool = True
    ) -> list[dict]:
        """
        Perform vector similarity search for articles.

        Args:
            embedding: Query embedding vector.
            threshold: Similarity threshold (0-1).
            limit: Maximum number of results.
            exclude_duplicates: Whether to exclude duplicate articles.

        Returns:
            List[Dict]: List of similar articles with similarity scores.
        """
        try:
            response = self.supabase.rpc(
                "match_articles",
                {
                    "query_embedding": embedding,
                    "match_threshold": threshold,
                    "match_count": limit
                }
            ).execute()

            results = response.data or []

            # Filter out duplicates if requested
            if exclude_duplicates:
                filtered_results = []
                for result in results:
                    # Check if article is marked as duplicate
                    article_check = self.supabase.table("articles").select(
                        "is_duplicate"
                    ).eq("id", result["id"]).single().execute()

                    if article_check.data and not article_check.data.get("is_duplicate", False):
                        filtered_results.append(result)

                results = filtered_results

            logger.debug(f"Found {len(results)} similar articles")
            return results

        except Exception as e:
            logger.error(f"Similarity search failed: {e}")
            return []

    async def get_top_articles_for_digest(
        self,
        since_hours: int = 24,
        min_relevance_score: float = 50.0,
        limit: int = 10
    ) -> list[Article]:
        """
        Get top articles for daily digest generation.

        Args:
            since_hours: Hours to look back for articles.
            min_relevance_score: Minimum relevance score.
            limit: Maximum number of articles.

        Returns:
            List[Article]: Top articles for digest.
        """
        try:
            since_date = datetime.utcnow() - timedelta(hours=since_hours)

            response = self.supabase.rpc(
                "get_top_articles_for_digest",
                {
                    "since_date": since_date.isoformat(),
                    "article_limit": limit
                }
            ).execute()

            articles = []
            for article_data in response.data:
                # Convert RPC result to Article
                article = Article(
                    id=UUID(article_data["id"]),
                    source_id="",  # Not needed for digest
                    source=ArticleSource(article_data["source"]),
                    title=article_data["title"],
                    content="",  # Not needed for digest
                    url=article_data["url"],
                    published_at=datetime.fromisoformat(
                        article_data["published_at"].replace("Z", "+00:00")
                    ),
                    summary=article_data["summary"],
                    relevance_score=article_data["relevance_score"]
                )
                articles.append(article)

            logger.debug(f"Retrieved {len(articles)} top articles for digest")
            return articles

        except Exception as e:
            logger.error(f"Failed to get top articles for digest: {e}")
            return []

    async def get_article_stats(self) -> dict[str, any]:
        """
        Get statistics about articles in the database.

        Returns:
            Dict: Article statistics.
        """
        try:
            # Total articles
            total_response = self.supabase.table("articles").select(
                "id", count="exact"
            ).execute()

            # Articles by source (using database-compatible source values)
            source_stats = {}
            for source in ArticleSource:
                # Map new sources to database enum for counting
                db_source = self._SOURCE_MAPPING.get(source, source)
                source_response = self.supabase.table("articles").select(
                    "id", count="exact"
                ).eq("source", db_source.value).execute()
                source_stats[source.value] = source_response.count or 0

            # Recent articles (last 24 hours)
            since_24h = datetime.utcnow() - timedelta(hours=24)
            recent_response = self.supabase.table("articles").select(
                "id", count="exact"
            ).gte("published_at", since_24h.isoformat()).execute()

            # Duplicates
            duplicates_response = self.supabase.table("articles").select(
                "id", count="exact"
            ).eq("is_duplicate", True).execute()

            return {
                "total_articles": total_response.count or 0,
                "articles_by_source": source_stats,
                "recent_24h": recent_response.count or 0,
                "duplicates": duplicates_response.count or 0,
                "last_updated": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to get article stats: {e}")
            return {"error": "Failed to retrieve statistics"}

    def _article_to_db_dict(self, article: Article) -> dict:
        """
        Convert Article model to database dictionary.

        Args:
            article: Article to convert.

        Returns:
            Dict: Database dictionary.
        """
        # Map new source types to existing database enum values
        db_source = self._SOURCE_MAPPING.get(article.source, article.source)
        
        data = {
            "source_id": article.source_id,
            "source": db_source.value,
            "title": article.title,
            "content": article.content,
            "url": article.url,
            "author": article.author,
            "published_at": article.published_at.isoformat(),
            "fetched_at": article.fetched_at.isoformat(),
            "summary": article.summary,
            "relevance_score": article.relevance_score,
            "categories": article.categories,
            "key_points": article.key_points,
            "is_duplicate": article.is_duplicate,
            "duplicate_of": str(article.duplicate_of) if article.duplicate_of else None
        }

        # Handle embedding
        if article.embedding:
            data["embedding"] = json.dumps(article.embedding)

        # Include ID if present
        if article.id:
            data["id"] = str(article.id)

        return data

    def _db_dict_to_article(self, data: dict) -> Article:
        """
        Convert database dictionary to Article model.

        Args:
            data: Database dictionary.

        Returns:
            Article: Article model.
        """
        # Parse embedding from JSON
        embedding = None
        if data.get("embedding"):
            try:
                embedding = json.loads(data["embedding"])
            except (json.JSONDecodeError, TypeError):
                embedding = None

        # Parse timestamps
        published_at = datetime.fromisoformat(
            data["published_at"].replace("Z", "+00:00")
        )
        fetched_at = datetime.fromisoformat(
            data["fetched_at"].replace("Z", "+00:00")
        )

        return Article(
            id=UUID(data["id"]) if data.get("id") else None,
            source_id=data["source_id"],
            source=ArticleSource(data["source"]),
            title=data["title"],
            content=data["content"],
            url=data["url"],
            author=data.get("author"),
            published_at=published_at,
            fetched_at=fetched_at,
            summary=data.get("summary"),
            relevance_score=data.get("relevance_score"),
            categories=data.get("categories", []),
            key_points=data.get("key_points", []),
            embedding=embedding,
            is_duplicate=data.get("is_duplicate", False),
            duplicate_of=UUID(data["duplicate_of"]) if data.get("duplicate_of") else None
        )
