"""
Article repository for database operations.

This module provides a data access layer for article operations
including CRUD operations, vector similarity search, and batch processing.
"""

import json
import logging
import re
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

    # Source mapping for database compatibility - preserves actual source in metadata
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
        self._metadata_column_exists = None  # Cache for metadata column check
        logger.info("Article repository initialized")

    def _sanitize_search_query(self, query: str) -> str:
        """
        Sanitize search query to prevent SQL injection.
        
        Args:
            query: Raw search query from user input.
            
        Returns:
            str: Sanitized query safe for database operations.
        """
        if not query or not isinstance(query, str):
            return ""

        # Remove dangerous SQL injection patterns
        dangerous_patterns = [
            r"';\s*--",  # Comment injection
            r"';\s*/\*",  # Block comment injection
            r"';\s*DROP",  # DROP statement injection
            r"';\s*DELETE",  # DELETE statement injection
            r"';\s*UPDATE",  # UPDATE statement injection
            r"';\s*INSERT",  # INSERT statement injection
            r"';\s*ALTER",  # ALTER statement injection
            r"';\s*CREATE",  # CREATE statement injection
            r"';\s*EXEC",  # EXEC statement injection
            r"xp_\w+",  # SQL Server extended procedures
            r"sp_\w+",  # SQL Server stored procedures
        ]

        sanitized = query.strip()

        # Remove dangerous patterns
        for pattern in dangerous_patterns:
            sanitized = re.sub(pattern, "", sanitized, flags=re.IGNORECASE)

        # Limit length to prevent DoS
        if len(sanitized) > 500:
            sanitized = sanitized[:500]

        # Remove multiple quotes that could be used for injection
        sanitized = re.sub(r"'{2,}", "'", sanitized)

        return sanitized

    def _check_metadata_column_exists(self) -> bool:
        """
        Check if the metadata column exists in the articles table.
        
        Returns:
            bool: True if metadata column exists.
        """
        if self._metadata_column_exists is None:
            try:
                # Try to query the metadata column
                result = self.supabase.table("articles").select("metadata").limit(1).execute()
                self._metadata_column_exists = True
                logger.debug("Metadata column exists in articles table")
            except Exception:
                self._metadata_column_exists = False
                logger.debug("Metadata column does not exist in articles table")

        return self._metadata_column_exists

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
        Create multiple articles in a single batch operation with upsert for duplicates.

        Args:
            articles: List of articles to create.

        Returns:
            List[Article]: List of created/updated articles.
        """
        if not articles:
            return []

        try:
            # Prepare batch data
            batch_data = []
            for article in articles:
                article_data = self._article_to_db_dict(article)
                batch_data.append(article_data)

            # Batch upsert - handle conflicts on (source, source_id) unique constraint
            response = self.supabase.table("articles").upsert(
                batch_data,
                on_conflict="source,source_id"
            ).execute()

            # Convert response back to Article models
            created_articles = []
            for article_data in response.data:
                article = self._db_dict_to_article(article_data)
                created_articles.append(article)

            logger.info(f"Batch upserted {len(created_articles)} articles (created or updated)")
            return created_articles

        except Exception as e:
            logger.error(f"Failed to batch create articles: {e}")
            # Fallback to individual inserts if batch upsert fails
            return await self._fallback_individual_upserts(articles)

    async def _fallback_individual_upserts(self, articles: list[Article]) -> list[Article]:
        """
        Fallback method to handle articles individually if batch upsert fails.
        
        Args:
            articles: List of articles to process.
            
        Returns:
            List[Article]: Successfully processed articles.
        """
        created_articles = []
        
        for article in articles:
            try:
                # Check if article exists
                existing = await self.find_by_source_id(article.source, article.source_id)
                
                if existing:
                    # Update existing article (only if new data is different)
                    if self._should_update_article(existing, article):
                        updated = await self.update_article(existing.id, {
                            "title": article.title,
                            "content": article.content,
                            "summary": article.summary,
                            "relevance_score": article.relevance_score,
                            "categories": article.categories,
                            "key_points": article.key_points,
                            "embedding": article.embedding
                        })
                        if updated:
                            created_articles.append(updated)
                    else:
                        # Article unchanged, add existing to result
                        created_articles.append(existing)
                else:
                    # Create new article
                    new_article = await self.create_article(article)
                    created_articles.append(new_article)
                    
            except Exception as e:
                logger.warning(f"Failed to process article '{article.title}': {e}")
                continue
                
        logger.info(f"Fallback processed {len(created_articles)}/{len(articles)} articles")
        return created_articles
    
    def _should_update_article(self, existing: Article, new: Article) -> bool:
        """
        Determine if an existing article should be updated with new data.
        
        Args:
            existing: Existing article from database.
            new: New article data.
            
        Returns:
            bool: True if update is needed.
        """
        # Update if content, summary, or analysis has changed
        return (
            existing.content != new.content or
            existing.summary != new.summary or
            existing.relevance_score != new.relevance_score or
            existing.categories != new.categories or
            existing.key_points != new.key_points or
            (new.embedding and existing.embedding != new.embedding)
        )

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

    async def search_articles(
        self,
        query: str,
        source: ArticleSource | None = None,
        limit: int = 20,
        offset: int = 0
    ) -> tuple[list[Article], int]:
        """
        Full-text search across article titles and content.
        
        Args:
            query: Search query text.
            source: Optional source filter.
            limit: Number of results.
            offset: Pagination offset.
            
        Returns:
            Tuple of (articles, total_count).
        """
        try:
            # Use RPC function for full-text search if available
            # Otherwise fall back to basic filtering
            params = {
                "query_text": query,
                "max_results": limit,
                "skip_results": offset
            }

            if source:
                params["source_filter"] = source.value

            # Try to use RPC function if it exists
            try:
                response = self.supabase.rpc("search_articles_fulltext", params).execute()

                articles = []
                total = 0

                for item in response.data:
                    article = self._db_dict_to_article(item)
                    articles.append(article)
                    if item.get("total_count"):
                        total = int(item["total_count"])

                return articles, total

            except Exception:
                # Fallback to basic search using ilike
                logger.debug("Full-text search function not available, using fallback")

                # Build query with basic text matching using safe parameterized queries
                sanitized_query = self._sanitize_search_query(query)
                search_pattern = f"%{sanitized_query}%"

                # Get total count first - using safe parameterized queries
                count_query = self.supabase.table("articles").select("id", count="exact")
                # Use separate ilike calls to avoid injection - Supabase client handles escaping
                count_query = count_query.or_(f"title.ilike.{search_pattern},content.ilike.{search_pattern}")

                if source:
                    count_query = count_query.eq("source", source.value)

                count_response = count_query.execute()
                total = count_response.count or 0

                # Get paginated results - using safe parameterized queries
                query_builder = self.supabase.table("articles").select("*")
                # Use separate ilike calls to avoid injection - Supabase client handles escaping
                query_builder = query_builder.or_(f"title.ilike.{search_pattern},content.ilike.{search_pattern}")

                if source:
                    query_builder = query_builder.eq("source", source.value)

                query_builder = query_builder.order("published_at", desc=True)
                query_builder = query_builder.range(offset, offset + limit - 1)

                response = query_builder.execute()

                articles = [self._db_dict_to_article(item) for item in response.data]

                return articles, total

        except Exception as e:
            logger.error(f"Search failed for query '{query}': {e}")
            return [], 0

    async def filter_articles(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        relevance_min: int | None = None,
        relevance_max: int | None = None,
        sources: list[ArticleSource] | None = None,
        categories: list[str] | None = None,
        limit: int = 20,
        offset: int = 0
    ) -> tuple[list[Article], int]:
        """
        Advanced filtering with multiple criteria.
        
        Args:
            start_date: Filter articles after this date.
            end_date: Filter articles before this date.
            relevance_min: Minimum relevance score.
            relevance_max: Maximum relevance score.
            sources: List of sources to include.
            categories: List of categories to filter by.
            limit: Number of results.
            offset: Pagination offset.
            
        Returns:
            Tuple of (articles, total_count).
        """
        try:
            # Build count query
            count_query = self.supabase.table("articles").select("id", count="exact")

            # Apply filters
            if start_date:
                count_query = count_query.gte("published_at", start_date.isoformat())
            if end_date:
                count_query = count_query.lte("published_at", end_date.isoformat())
            if relevance_min is not None:
                count_query = count_query.gte("relevance_score", relevance_min)
            if relevance_max is not None:
                count_query = count_query.lte("relevance_score", relevance_max)
            if sources:
                source_values = [s.value for s in sources]
                count_query = count_query.in_("source", source_values)
            if categories:
                # For array contains, we need to use contains
                for category in categories:
                    count_query = count_query.contains("categories", [category])

            count_query = count_query.eq("is_duplicate", False)
            count_response = count_query.execute()
            total = count_response.count or 0

            # Build data query with same filters
            data_query = self.supabase.table("articles").select("*")

            if start_date:
                data_query = data_query.gte("published_at", start_date.isoformat())
            if end_date:
                data_query = data_query.lte("published_at", end_date.isoformat())
            if relevance_min is not None:
                data_query = data_query.gte("relevance_score", relevance_min)
            if relevance_max is not None:
                data_query = data_query.lte("relevance_score", relevance_max)
            if sources:
                source_values = [s.value for s in sources]
                data_query = data_query.in_("source", source_values)
            if categories:
                for category in categories:
                    data_query = data_query.contains("categories", [category])

            data_query = data_query.eq("is_duplicate", False)
            data_query = data_query.order("published_at", desc=True)
            data_query = data_query.range(offset, offset + limit - 1)

            response = data_query.execute()

            articles = [self._db_dict_to_article(item) for item in response.data]

            return articles, total

        except Exception as e:
            logger.error(f"Filter articles failed: {e}")
            return [], 0

    async def get_articles_paginated(
        self,
        page: int = 1,
        per_page: int = 20,
        sort_by: str = "published_at",
        order: str = "desc",
        source: ArticleSource | None = None
    ) -> tuple[list[Article], int]:
        """
        Get paginated articles with enhanced pagination metadata.
        
        Args:
            page: Page number (1-indexed).
            per_page: Items per page.
            sort_by: Field to sort by.
            order: Sort order (asc/desc).
            source: Optional source filter.
            
        Returns:
            Tuple of (articles, total_count).
        """
        try:
            # Calculate offset from page number
            offset = (page - 1) * per_page

            # Build count query
            count_query = self.supabase.table("articles").select("id", count="exact")
            count_query = count_query.eq("is_duplicate", False)

            if source:
                count_query = count_query.eq("source", source.value)

            count_response = count_query.execute()
            total = count_response.count or 0

            # Build data query
            data_query = self.supabase.table("articles").select("*")
            data_query = data_query.eq("is_duplicate", False)

            if source:
                data_query = data_query.eq("source", source.value)

            # Apply sorting
            desc_order = order.lower() == "desc"
            data_query = data_query.order(sort_by, desc=desc_order)
            data_query = data_query.range(offset, offset + per_page - 1)

            response = data_query.execute()

            articles = [self._db_dict_to_article(item) for item in response.data]

            return articles, total

        except Exception as e:
            logger.error(f"Get paginated articles failed: {e}")
            return [], 0

    async def get_sources_metadata(self) -> list[dict]:
        """
        Get metadata about all sources including article counts.
        
        Returns:
            List of source metadata dictionaries.
        """
        try:
            # Try to use RPC function if available
            try:
                response = self.supabase.rpc("get_sources_metadata").execute()

                # Enhance with display names and descriptions
                sources_info = []
                for item in response.data:
                    source_enum = ArticleSource(item["source_name"])
                    sources_info.append({
                        "name": source_enum.value,
                        "display_name": self._get_source_display_name(source_enum),
                        "description": self._get_source_description(source_enum),
                        "article_count": item["article_count"],
                        "last_published": item.get("last_published"),
                        "avg_relevance_score": float(item.get("avg_relevance_score", 0)),
                        "status": "active",
                        "icon_url": f"/icons/{source_enum.value}.svg"
                    })

                return sources_info

            except Exception:
                # Fallback to manual aggregation
                logger.debug("Sources metadata function not available, using fallback")

                sources_info = []
                for source in ArticleSource:
                    # Get count for this source
                    count_response = self.supabase.table("articles").select(
                        "id, published_at, relevance_score", count="exact"
                    ).eq("source", source.value).eq("is_duplicate", False).execute()

                    # Get last published date and avg relevance
                    if count_response.data:
                        articles_data = count_response.data
                        last_published = max(
                            (a["published_at"] for a in articles_data),
                            default=None
                        )
                        avg_relevance = sum(
                            a.get("relevance_score", 0) for a in articles_data if a.get("relevance_score")
                        ) / len(articles_data) if articles_data else 0
                    else:
                        last_published = None
                        avg_relevance = 0

                    sources_info.append({
                        "name": source.value,
                        "display_name": self._get_source_display_name(source),
                        "description": self._get_source_description(source),
                        "article_count": count_response.count or 0,
                        "last_published": last_published,
                        "avg_relevance_score": round(avg_relevance, 2),
                        "status": "active",
                        "icon_url": f"/icons/{source.value}.svg"
                    })

                return sources_info

        except Exception as e:
            logger.error(f"Get sources metadata failed: {e}")
            return []

    async def get_digests(
        self,
        page: int = 1,
        per_page: int = 10
    ) -> tuple[list[dict], int]:
        """
        Get paginated list of daily digests.
        
        Args:
            page: Page number (1-indexed).
            per_page: Items per page.
            
        Returns:
            Tuple of (digests, total_count).
        """
        try:
            # Calculate offset
            offset = (page - 1) * per_page

            # Get total count
            count_response = self.supabase.table("daily_digests").select(
                "id", count="exact"
            ).execute()
            total = count_response.count or 0

            # Get paginated digests
            response = self.supabase.table("daily_digests").select(
                "*, digest_articles(article_id)"
            ).order("digest_date", desc=True).range(
                offset, offset + per_page - 1
            ).execute()

            digests = []
            for digest_data in response.data:
                # Count articles in this digest
                article_count = len(digest_data.get("digest_articles", []))

                # Extract key developments from summary
                summary = digest_data["summary_text"]
                key_developments = self._extract_key_developments(summary)

                digests.append({
                    "id": digest_data["id"],
                    "date": digest_data["digest_date"],
                    "title": f"AI Daily: {digest_data['digest_date']}",
                    "summary": summary,
                    "key_developments": key_developments,
                    "article_count": article_count,
                    "audio_url": digest_data.get("audio_url"),
                    "audio_duration": None,  # Would need to be stored or calculated
                    "created_at": digest_data["created_at"]
                })

            return digests, total

        except Exception as e:
            logger.error(f"Get digests failed: {e}")
            return [], 0

    async def get_digest_by_id(self, digest_id: UUID) -> dict | None:
        """
        Get a single digest with all its articles.
        
        Args:
            digest_id: Digest ID.
            
        Returns:
            Digest dictionary with articles, or None if not found.
        """
        try:
            # Get digest with related articles
            response = self.supabase.table("daily_digests").select(
                "*, digest_articles(article_id)"
            ).eq("id", str(digest_id)).single().execute()

            if not response.data:
                return None

            digest_data = response.data

            # Get full article details for this digest
            article_ids = [item["article_id"] for item in digest_data.get("digest_articles", [])]

            articles = []
            if article_ids:
                articles_response = self.supabase.table("articles").select(
                    "id, title, summary, source, url, relevance_score"
                ).in_("id", article_ids).execute()

                articles = articles_response.data

            # Extract key developments
            key_developments = self._extract_key_developments(digest_data["summary_text"])

            return {
                "id": digest_data["id"],
                "date": digest_data["digest_date"],
                "title": f"AI Daily: {digest_data['digest_date']}",
                "summary": digest_data["summary_text"],
                "key_developments": key_developments,
                "articles": articles,
                "audio_url": digest_data.get("audio_url"),
                "audio_duration": None,
                "created_at": digest_data["created_at"],
                "updated_at": digest_data.get("updated_at", digest_data["created_at"])
            }

        except Exception as e:
            logger.error(f"Get digest by ID failed: {e}")
            return None

    def _get_source_display_name(self, source: ArticleSource) -> str:
        """Get display name for a source."""
        display_names = {
            ArticleSource.ARXIV: "ArXiv",
            ArticleSource.HACKERNEWS: "Hacker News",
            ArticleSource.RSS: "RSS Feeds",
            ArticleSource.YOUTUBE: "YouTube",
            ArticleSource.REDDIT: "Reddit",
            ArticleSource.GITHUB: "GitHub",
            ArticleSource.HUGGINGFACE: "Hugging Face"
        }
        return display_names.get(source, source.value.title())

    def _get_source_description(self, source: ArticleSource) -> str:
        """Get description for a source."""
        descriptions = {
            ArticleSource.ARXIV: "Academic papers and preprints",
            ArticleSource.HACKERNEWS: "Technology and startup news",
            ArticleSource.RSS: "Curated RSS feed articles",
            ArticleSource.YOUTUBE: "Video content and tutorials",
            ArticleSource.REDDIT: "Community discussions",
            ArticleSource.GITHUB: "Open source projects and releases",
            ArticleSource.HUGGINGFACE: "ML models and datasets"
        }
        return descriptions.get(source, "Content aggregation source")

    def _extract_key_developments(self, summary: str, max_points: int = 3) -> list[str]:
        """Extract key developments from a summary text."""
        # Simple extraction - split by sentences and take first few
        # In production, this could use AI or more sophisticated parsing
        sentences = summary.split(". ")
        key_points = []

        for sentence in sentences[:max_points]:
            if len(sentence) > 20:  # Filter out very short sentences
                clean_sentence = sentence.strip()
                if not clean_sentence.endswith("."):
                    clean_sentence += "."
                key_points.append(clean_sentence)

        return key_points if key_points else ["Daily AI news summary"]

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

        # Preserve actual source type in metadata if it's being mapped
        metadata = dict(article.metadata)  # Copy existing metadata
        if article.source in self._SOURCE_MAPPING:
            metadata["_actual_source"] = article.source.value

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

        # Include metadata if column exists
        if self._check_metadata_column_exists():
            data["metadata"] = metadata

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

        # Parse metadata and restore actual source if available
        metadata = data.get("metadata", {})
        if isinstance(metadata, str):
            try:
                metadata = json.loads(metadata)
            except (json.JSONDecodeError, TypeError):
                metadata = {}

        # Restore actual source from metadata if it was mapped
        actual_source = metadata.get("_actual_source")
        if actual_source:
            source = ArticleSource(actual_source)
            # Remove the internal field from metadata
            metadata = {k: v for k, v in metadata.items() if k != "_actual_source"}
        else:
            source = ArticleSource(data["source"])

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
            source=source,
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
            duplicate_of=UUID(data["duplicate_of"]) if data.get("duplicate_of") else None,
            metadata=metadata
        )
