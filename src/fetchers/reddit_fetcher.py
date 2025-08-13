"""
Reddit fetcher for AI/ML community discussions.

This module implements fetching from Reddit using asyncpraw with filtering
for high-quality posts and community engagement metrics.
"""

import asyncio
import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

try:
    import asyncpraw
    import asyncpraw.models
except ImportError:
    asyncpraw = None

from ..models.articles import Article, ArticleSource
from .base import BaseFetcher, FetchError

logger = logging.getLogger(__name__)


class RedditFetcher(BaseFetcher):
    """
    Fetcher for Reddit AI/ML subreddits.
    
    Fetches high-quality posts and discussions with engagement filtering
    and community insights extraction.
    """

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        user_agent: str,
        username: str | None = None
    ):
        """
        Initialize Reddit fetcher.
        
        Args:
            client_id: Reddit OAuth client ID.
            client_secret: Reddit OAuth client secret.
            user_agent: User agent string for API requests.
            username: Reddit username (optional, for user agent).
        """
        if asyncpraw is None:
            raise ImportError("asyncpraw is required for Reddit fetching. Install with: pip install asyncpraw")

        # 60 requests per minute = 1 second delay
        super().__init__(source=ArticleSource.REDDIT, rate_limit_delay=1.0)

        # Format user agent properly
        if username:
            self.user_agent = f"AI-News-Aggregator/1.0 (by /u/{username})"
        else:
            self.user_agent = user_agent

        self.reddit = asyncpraw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=self.user_agent
        )

        self.subreddits = self._load_subreddits()
        self.min_upvotes = 50
        self.min_comments = 10

        logger.info(f"Reddit fetcher initialized for {len(self.subreddits)} subreddits")

    def _load_subreddits(self) -> list[str]:
        """Load subreddits from config file."""
        config_path = Path(__file__).parent.parent.parent / "config" / "reddit_subs.json"

        try:
            with open(config_path) as f:
                subs = json.load(f)
                logger.debug(f"Loaded {len(subs)} subreddits from config")
                return subs
        except FileNotFoundError:
            logger.warning(f"Config file not found at {config_path}, using default")
            return ["LocalLLaMA"]
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in config file: {e}")
            return ["LocalLLaMA"]

    async def fetch(self, max_articles: int = 50) -> list[Article]:
        """
        Fetch quality posts from configured subreddits.
        
        Args:
            max_articles: Maximum number of articles to return.
            
        Returns:
            List[Article]: List of Reddit post articles.
            
        Raises:
            FetchError: If fetching fails.
        """
        try:
            logger.info(f"Fetching posts from {len(self.subreddits)} subreddits")
            all_articles = []

            # Fetch from each subreddit
            articles_per_sub = max(max_articles // len(self.subreddits), 10)

            for subreddit_name in self.subreddits:
                try:
                    logger.debug(f"Fetching from r/{subreddit_name}")
                    subreddit = await self.reddit.subreddit(subreddit_name)

                    # Fetch from multiple streams concurrently
                    hot_task = self._fetch_from_stream(subreddit.hot(limit=50), "hot")
                    top_day_task = self._fetch_from_stream(subreddit.top(time_filter="day", limit=25), "top_day")
                    top_week_task = self._fetch_from_stream(subreddit.top(time_filter="week", limit=25), "top_week")

                    hot_posts, top_day_posts, top_week_posts = await asyncio.gather(
                        hot_task, top_day_task, top_week_task, return_exceptions=True
                    )

                    # Handle exceptions
                    all_posts = []
                    for posts, stream_name in [(hot_posts, "hot"), (top_day_posts, "top_day"), (top_week_posts, "top_week")]:
                        if isinstance(posts, Exception):
                            logger.warning(f"Failed to fetch {stream_name} posts from r/{subreddit_name}: {posts}")
                        else:
                            all_posts.extend(posts)

                    # Deduplicate posts by ID
                    seen_ids = set()
                    unique_posts = []
                    for post in all_posts:
                        if post.id not in seen_ids:
                            unique_posts.append(post)
                            seen_ids.add(post.id)

                    # Convert to articles with filtering
                    for post in unique_posts[:articles_per_sub]:
                        if self._is_quality_post(post):
                            try:
                                article = await self._submission_to_article(post)
                                if article:
                                    # Add subreddit to metadata
                                    article.metadata['subreddit'] = subreddit_name
                                    all_articles.append(article)
                            except Exception as e:
                                logger.warning(f"Failed to convert post {post.id}: {e}")
                                continue

                except Exception as e:
                    logger.warning(f"Failed to fetch from r/{subreddit_name}: {e}")
                    continue

            # Sort all articles by engagement score and limit results
            all_articles.sort(key=lambda x: x.metadata.get('engagement_score', 0), reverse=True)
            limited_articles = all_articles[:max_articles]

            logger.info(f"Successfully fetched {len(limited_articles)} articles from {len(self.subreddits)} subreddits")
            return limited_articles

        except Exception as e:
            error_msg = f"Failed to fetch from Reddit: {str(e)}"
            logger.error(error_msg)
            raise FetchError(error_msg, source=self.source)
        finally:
            # Clean up Reddit connection
            try:
                await self.reddit.close()
            except Exception as e:
                logger.debug(f"Error closing Reddit connection: {e}")

    async def _fetch_from_stream(
        self,
        stream,
        stream_name: str
    ) -> list[Any]:
        """
        Fetch posts from a Reddit stream.
        
        Args:
            stream: Reddit stream (hot, top, etc.).
            stream_name: Name of the stream for logging.
            
        Returns:
            List of Reddit submissions.
        """
        posts = []
        try:
            async for submission in stream:
                # Apply rate limiting
                await self._apply_rate_limit()
                posts.append(submission)

            logger.debug(f"Fetched {len(posts)} posts from {stream_name} stream")
            return posts

        except Exception as e:
            logger.warning(f"Error fetching from {stream_name} stream: {e}")
            return posts

    def _is_quality_post(self, submission: Any) -> bool:
        """
        Check if a post meets quality criteria.
        
        Args:
            submission: Reddit submission.
            
        Returns:
            bool: True if post meets quality criteria.
        """
        # Skip stickied/pinned posts
        if getattr(submission, 'stickied', False):
            return False

        # Skip deleted or removed posts
        if getattr(submission, 'selftext', '') == '[deleted]' or getattr(submission, 'selftext', '') == '[removed]':
            return False

        # Check engagement thresholds
        upvotes = getattr(submission, 'score', 0)
        comments = getattr(submission, 'num_comments', 0)

        # Either high upvotes OR decent comments (quality discussion)
        meets_threshold = upvotes >= self.min_upvotes or comments >= self.min_comments

        # Additional quality indicators
        upvote_ratio = getattr(submission, 'upvote_ratio', 0)
        has_good_ratio = upvote_ratio >= 0.7  # At least 70% upvoted

        # Check for meaningful content
        title_length = len(getattr(submission, 'title', ''))
        has_content = title_length > 10  # At least some meaningful title

        return meets_threshold and has_good_ratio and has_content

    async def _submission_to_article(self, submission: Any) -> Article | None:
        """
        Convert Reddit submission to Article object.
        
        Args:
            submission: Reddit submission.
            
        Returns:
            Article: Converted article or None if conversion fails.
        """
        try:
            # Get submission ID
            post_id = getattr(submission, 'id', '')
            if not post_id:
                return None

            # Create title with Reddit prefix
            title = f"💬 {getattr(submission, 'title', 'Untitled Post')}"

            # Create content from post text and metadata
            content = ""

            # Add post flair if available
            flair = getattr(submission, 'link_flair_text', '')
            if flair:
                content += f"[{flair}] "

            # Add selftext if available
            selftext = getattr(submission, 'selftext', '')
            if selftext and selftext not in ['[deleted]', '[removed]', '']:
                # Truncate long posts
                if len(selftext) > 500:
                    content += selftext[:500] + "..."
                else:
                    content += selftext
            else:
                # For link posts, use title and basic info
                content += f"Discussion: {getattr(submission, 'title', '')}"

            # Create URL
            url = f"https://reddit.com{getattr(submission, 'permalink', '')}"

            # Extract author
            author_name = getattr(submission, 'author', None)
            if author_name:
                author = f"u/{author_name}"
            else:
                author = "Reddit User"

            # Parse published date
            published_at = self._parse_reddit_date(submission)

            # Extract metadata
            metadata = await self._extract_reddit_metadata(submission)

            return Article(
                source_id=f"reddit_{post_id}",
                source=ArticleSource.REDDIT,
                title=title,
                content=content,
                url=url,
                author=author,
                published_at=published_at,
                fetched_at=datetime.now(UTC),
                metadata=metadata,
                summary=None,
                relevance_score=None,
                embedding=None,
                is_duplicate=False,
                duplicate_of=None
            )

        except Exception as e:
            logger.warning(f"Failed to convert submission {getattr(submission, 'id', 'unknown')}: {e}")
            return None

    def _parse_reddit_date(self, submission: Any) -> datetime:
        """
        Parse Reddit submission date.
        
        Args:
            submission: Reddit submission.
            
        Returns:
            datetime: Parsed date or current time if parsing fails.
        """
        try:
            created_utc = getattr(submission, 'created_utc', None)
            if created_utc:
                return datetime.fromtimestamp(created_utc, tz=UTC)
        except (ValueError, TypeError, AttributeError) as e:
            logger.debug(f"Failed to parse Reddit date: {e}")

        # Fallback to current time
        return datetime.now(UTC)

    async def _extract_reddit_metadata(self, submission: Any) -> dict[str, Any]:
        """
        Extract Reddit-specific metadata.
        
        Args:
            submission: Reddit submission.
            
        Returns:
            dict: Extracted metadata.
        """
        metadata = {
            "platform": "reddit",
            "subreddit": "",  # Will be set per article in fetch method
            "post_id": getattr(submission, 'id', ''),
            "upvotes": getattr(submission, 'score', 0),
            "comments": getattr(submission, 'num_comments', 0),
            "upvote_ratio": getattr(submission, 'upvote_ratio', 0),
        }

        # Add post flair
        flair = getattr(submission, 'link_flair_text', '')
        if flair:
            metadata["flair"] = flair

        # Add post type
        is_self = getattr(submission, 'is_self', False)
        metadata["post_type"] = "text" if is_self else "link"

        # Add domain for link posts
        if not is_self:
            domain = getattr(submission, 'domain', '')
            if domain:
                metadata["domain"] = domain

        # Calculate engagement score
        upvotes = metadata["upvotes"]
        comments = metadata["comments"]
        ratio = metadata["upvote_ratio"]

        # Simple engagement scoring algorithm
        engagement_score = (upvotes * ratio) + (comments * 2)
        metadata["engagement_score"] = int(engagement_score)

        # Add awards if available
        try:
            total_awards = getattr(submission, 'total_awards_received', 0)
            if total_awards > 0:
                metadata["awards"] = total_awards
        except AttributeError:
            pass

        # Check if post is distinguished (mod post, etc.)
        distinguished = getattr(submission, 'distinguished', None)
        if distinguished:
            metadata["distinguished"] = distinguished

        return metadata
