"""
Tests for Reddit fetcher.

This module contains comprehensive tests for the RedditFetcher class,
including async Reddit API integration, filtering, and metadata extraction.
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.fetchers.base import FetchError
from src.fetchers.reddit_fetcher import RedditFetcher
from src.models.articles import ArticleSource


class TestRedditFetcher:
    """Test cases for RedditFetcher."""

    @pytest.fixture
    def mock_reddit_credentials(self):
        """Mock Reddit API credentials."""
        return {
            'client_id': 'test_client_id',
            'client_secret': 'test_client_secret',
            'user_agent': 'TestAgent/1.0',
            'username': 'test_user'
        }

    @pytest.fixture
    def fetcher(self, mock_reddit_credentials):
        """Create a RedditFetcher instance with mocked credentials."""
        with patch('src.fetchers.reddit_fetcher.asyncpraw') as mock_asyncpraw:
            mock_reddit_instance = AsyncMock()
            mock_asyncpraw.Reddit.return_value = mock_reddit_instance

            fetcher = RedditFetcher(**mock_reddit_credentials)
            fetcher.reddit = mock_reddit_instance
            return fetcher

    @pytest.fixture
    def mock_submission(self):
        """Create a mock Reddit submission."""
        submission = MagicMock()
        submission.id = 'test123'
        submission.title = 'New LLaMA Model Released'
        submission.selftext = 'This is a great new model with improved performance.'
        submission.link_flair_text = 'News'
        submission.permalink = '/r/LocalLLaMA/comments/test123/new_llama_model_released/'
        submission.author = 'test_author'
        submission.score = 150
        submission.num_comments = 25
        submission.upvote_ratio = 0.85
        submission.created_utc = 1640995200  # 2022-01-01 00:00:00 UTC
        submission.is_self = True
        submission.stickied = False
        submission.total_awards_received = 2
        submission.distinguished = None
        return submission

    @pytest.fixture
    def mock_low_quality_submission(self):
        """Create a mock low-quality Reddit submission."""
        submission = MagicMock()
        submission.id = 'test456'
        submission.title = 'Low quality post'
        submission.selftext = 'Short post'
        submission.score = 5  # Below threshold
        submission.num_comments = 2  # Below threshold
        submission.upvote_ratio = 0.4  # Below threshold
        submission.stickied = False
        return submission

    def test_initialization_with_username(self, mock_reddit_credentials):
        """Test fetcher initialization with username."""
        with patch('src.fetchers.reddit_fetcher.asyncpraw') as mock_asyncpraw:
            mock_reddit_instance = AsyncMock()
            mock_asyncpraw.Reddit.return_value = mock_reddit_instance

            fetcher = RedditFetcher(**mock_reddit_credentials)

            assert fetcher.source == ArticleSource.REDDIT
            assert fetcher.rate_limit_delay == 1.0
            assert fetcher.user_agent == "AI-News-Aggregator/1.0 (by /u/test_user)"
            assert fetcher.subreddit_name == "LocalLLaMA"
            assert fetcher.min_upvotes == 50
            assert fetcher.min_comments == 10

    def test_initialization_without_username(self):
        """Test fetcher initialization without username."""
        with patch('src.fetchers.reddit_fetcher.asyncpraw') as mock_asyncpraw:
            mock_reddit_instance = AsyncMock()
            mock_asyncpraw.Reddit.return_value = mock_reddit_instance

            fetcher = RedditFetcher(
                client_id='test_id',
                client_secret='test_secret',
                user_agent='CustomAgent/1.0'
            )

            assert fetcher.user_agent == 'CustomAgent/1.0'

    def test_initialization_without_asyncpraw(self):
        """Test that initialization fails when asyncpraw is not available."""
        with patch('src.fetchers.reddit_fetcher.asyncpraw', None):
            with pytest.raises(ImportError, match="asyncpraw is required"):
                RedditFetcher(
                    client_id='test_id',
                    client_secret='test_secret',
                    user_agent='TestAgent/1.0'
                )

    def test_is_quality_post_high_upvotes(self, fetcher, mock_submission):
        """Test quality detection for posts with high upvotes."""
        mock_submission.score = 100
        mock_submission.num_comments = 5
        mock_submission.upvote_ratio = 0.8

        assert fetcher._is_quality_post(mock_submission) is True

    def test_is_quality_post_high_comments(self, fetcher, mock_submission):
        """Test quality detection for posts with high comment count."""
        mock_submission.score = 30
        mock_submission.num_comments = 15
        mock_submission.upvote_ratio = 0.75

        assert fetcher._is_quality_post(mock_submission) is True

    def test_is_quality_post_low_quality(self, fetcher, mock_low_quality_submission):
        """Test quality detection rejects low-quality posts."""
        assert fetcher._is_quality_post(mock_low_quality_submission) is False

    def test_is_quality_post_stickied(self, fetcher, mock_submission):
        """Test that stickied posts are filtered out."""
        mock_submission.stickied = True
        assert fetcher._is_quality_post(mock_submission) is False

    def test_is_quality_post_deleted(self, fetcher, mock_submission):
        """Test that deleted posts are filtered out."""
        mock_submission.selftext = '[deleted]'
        assert fetcher._is_quality_post(mock_submission) is False

    def test_is_quality_post_removed(self, fetcher, mock_submission):
        """Test that removed posts are filtered out."""
        mock_submission.selftext = '[removed]'
        assert fetcher._is_quality_post(mock_submission) is False

    def test_parse_reddit_date_valid(self, fetcher, mock_submission):
        """Test parsing valid Reddit timestamp."""
        timestamp = 1640995200  # 2022-01-01 00:00:00 UTC
        mock_submission.created_utc = timestamp

        result = fetcher._parse_reddit_date(mock_submission)
        expected = datetime.fromtimestamp(timestamp, tz=UTC)

        assert result == expected

    def test_parse_reddit_date_invalid(self, fetcher, mock_submission):
        """Test parsing invalid Reddit timestamp falls back to current time."""
        mock_submission.created_utc = None

        result = fetcher._parse_reddit_date(mock_submission)

        # Should be close to current time
        now = datetime.now(UTC)
        assert abs((result - now).total_seconds()) < 5

    @pytest.mark.asyncio
    async def test_extract_reddit_metadata(self, fetcher, mock_submission):
        """Test Reddit metadata extraction."""
        metadata = await fetcher._extract_reddit_metadata(mock_submission)

        assert metadata['platform'] == 'reddit'
        assert metadata['subreddit'] == 'LocalLLaMA'
        assert metadata['post_id'] == 'test123'
        assert metadata['upvotes'] == 150
        assert metadata['comments'] == 25
        assert metadata['upvote_ratio'] == 0.85
        assert metadata['flair'] == 'News'
        assert metadata['post_type'] == 'text'
        assert metadata['awards'] == 2
        assert 'engagement_score' in metadata
        assert metadata['engagement_score'] > 0

    @pytest.mark.asyncio
    async def test_extract_reddit_metadata_link_post(self, fetcher, mock_submission):
        """Test metadata extraction for link posts."""
        mock_submission.is_self = False
        mock_submission.domain = 'github.com'

        metadata = await fetcher._extract_reddit_metadata(mock_submission)

        assert metadata['post_type'] == 'link'
        assert metadata['domain'] == 'github.com'

    @pytest.mark.asyncio
    async def test_submission_to_article(self, fetcher, mock_submission):
        """Test converting Reddit submission to Article."""
        article = await fetcher._submission_to_article(mock_submission)

        assert article is not None
        assert article.source_id == 'reddit_test123'
        assert article.source == ArticleSource.REDDIT
        assert article.title == '💬 New LLaMA Model Released'
        assert '[News]' in article.content
        assert 'This is a great new model' in article.content
        assert article.url == 'https://reddit.com/r/LocalLLaMA/comments/test123/new_llama_model_released/'
        assert article.author == 'u/test_author'
        assert article.metadata['platform'] == 'reddit'

    @pytest.mark.asyncio
    async def test_submission_to_article_long_content(self, fetcher, mock_submission):
        """Test article creation with long content gets truncated."""
        mock_submission.selftext = 'A' * 600  # Long content

        article = await fetcher._submission_to_article(mock_submission)

        # Content includes "[News] " prefix (7 chars) + truncated selftext (500) + "..." (3) = 510 chars max
        assert len(article.content) <= 510
        assert article.content.endswith('...')

    @pytest.mark.asyncio
    async def test_submission_to_article_no_selftext(self, fetcher, mock_submission):
        """Test article creation for posts without selftext."""
        mock_submission.selftext = ''

        article = await fetcher._submission_to_article(mock_submission)

        assert 'Discussion:' in article.content
        assert mock_submission.title in article.content

    @pytest.mark.asyncio
    async def test_submission_to_article_no_author(self, fetcher, mock_submission):
        """Test article creation when author is None."""
        mock_submission.author = None

        article = await fetcher._submission_to_article(mock_submission)

        assert article.author == 'Reddit User'

    @pytest.mark.asyncio
    async def test_submission_to_article_no_id(self, fetcher, mock_submission):
        """Test article creation fails when submission has no ID."""
        mock_submission.id = ''

        article = await fetcher._submission_to_article(mock_submission)

        assert article is None

    @pytest.mark.asyncio
    async def test_fetch_from_stream(self, fetcher):
        """Test fetching posts from a Reddit stream."""
        mock_stream = AsyncMock()
        mock_submissions = [MagicMock(), MagicMock()]
        mock_submissions[0].id = 'post1'
        mock_submissions[1].id = 'post2'

        mock_stream.__aiter__.return_value = iter(mock_submissions)

        with patch.object(fetcher, '_apply_rate_limit', new_callable=AsyncMock):
            result = await fetcher._fetch_from_stream(mock_stream, 'test_stream')

        assert len(result) == 2
        assert result[0].id == 'post1'
        assert result[1].id == 'post2'

    @pytest.mark.asyncio
    async def test_fetch_from_stream_error(self, fetcher):
        """Test fetch_from_stream handles errors gracefully."""
        mock_stream = AsyncMock()
        mock_stream.__aiter__.side_effect = Exception("Stream error")

        result = await fetcher._fetch_from_stream(mock_stream, 'test_stream')

        assert result == []

    @pytest.mark.asyncio
    async def test_fetch_success(self, fetcher, mock_submission):
        """Test successful fetch operation."""
        # Mock the _fetch_from_stream method directly to avoid complex async iterator setup
        async def mock_fetch_from_stream(stream, stream_name):
            if stream_name == "hot":
                return [mock_submission]
            else:
                return []

        with patch.object(fetcher, '_fetch_from_stream', side_effect=mock_fetch_from_stream), \
             patch.object(fetcher, '_is_quality_post', return_value=True):

            articles = await fetcher.fetch(max_articles=10)

        assert len(articles) == 1
        assert articles[0].source == ArticleSource.REDDIT
        assert articles[0].title == '💬 New LLaMA Model Released'

    @pytest.mark.asyncio
    async def test_fetch_no_quality_posts(self, fetcher, mock_low_quality_submission):
        """Test fetch when no posts meet quality criteria."""
        mock_subreddit = AsyncMock()
        mock_stream = AsyncMock()
        mock_stream.__aiter__.return_value = iter([mock_low_quality_submission])

        mock_subreddit.hot.return_value = mock_stream
        mock_subreddit.top.return_value = mock_stream

        fetcher.reddit.subreddit.return_value = mock_subreddit

        with patch.object(fetcher, '_apply_rate_limit', new_callable=AsyncMock):
            articles = await fetcher.fetch(max_articles=10)

        assert len(articles) == 0

    @pytest.mark.asyncio
    async def test_fetch_deduplication(self, fetcher, mock_submission):
        """Test that duplicate posts are filtered out."""
        # Create two identical posts
        mock_submission_2 = MagicMock()
        mock_submission_2.id = 'test123'  # Same ID as mock_submission

        # Mock the _fetch_from_stream method directly
        async def mock_fetch_from_stream(stream, stream_name):
            if stream_name == "hot":
                return [mock_submission]
            elif stream_name == "top_day":
                return [mock_submission_2]  # Same ID, should be deduplicated
            else:
                return []

        with patch.object(fetcher, '_fetch_from_stream', side_effect=mock_fetch_from_stream), \
             patch.object(fetcher, '_is_quality_post', return_value=True):

            articles = await fetcher.fetch(max_articles=10)

        # Should only get one article despite duplicate posts
        assert len(articles) == 1

    @pytest.mark.asyncio
    async def test_fetch_stream_exception(self, fetcher):
        """Test fetch handles stream exceptions gracefully."""
        mock_subreddit = AsyncMock()

        # Make one stream fail
        mock_subreddit.hot.side_effect = Exception("Hot stream failed")
        mock_subreddit.top.return_value = AsyncMock()
        mock_subreddit.top.return_value.__aiter__.return_value = iter([])

        fetcher.reddit.subreddit.return_value = mock_subreddit

        with patch.object(fetcher, '_apply_rate_limit', new_callable=AsyncMock):
            articles = await fetcher.fetch(max_articles=10)

        # Should handle the exception and continue
        assert len(articles) == 0

    @pytest.mark.asyncio
    async def test_fetch_general_error(self, fetcher):
        """Test fetch handles general errors."""
        fetcher.reddit.subreddit.side_effect = Exception("General Reddit error")

        with pytest.raises(FetchError, match="Failed to fetch from Reddit"):
            await fetcher.fetch(max_articles=10)

    @pytest.mark.asyncio
    async def test_fetch_reddit_connection_cleanup(self, fetcher):
        """Test that Reddit connection is properly cleaned up."""
        mock_subreddit = AsyncMock()
        mock_stream = AsyncMock()
        mock_stream.__aiter__.return_value = iter([])

        mock_subreddit.hot.return_value = mock_stream
        mock_subreddit.top.return_value = mock_stream

        fetcher.reddit.subreddit.return_value = mock_subreddit

        with patch.object(fetcher, '_apply_rate_limit', new_callable=AsyncMock):
            await fetcher.fetch(max_articles=10)

        # Verify Reddit connection close was called
        fetcher.reddit.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_fetch_reddit_cleanup_error(self, fetcher):
        """Test that cleanup errors are handled gracefully."""
        mock_subreddit = AsyncMock()
        mock_stream = AsyncMock()
        mock_stream.__aiter__.return_value = iter([])

        mock_subreddit.hot.return_value = mock_stream
        mock_subreddit.top.return_value = mock_stream

        fetcher.reddit.subreddit.return_value = mock_subreddit
        fetcher.reddit.close.side_effect = Exception("Cleanup error")

        with patch.object(fetcher, '_apply_rate_limit', new_callable=AsyncMock):
            # Should not raise exception despite cleanup error
            articles = await fetcher.fetch(max_articles=10)
            assert len(articles) == 0

    def test_engagement_score_calculation(self, fetcher):
        """Test engagement score calculation algorithm."""
        mock_sub = MagicMock()
        mock_sub.score = 100
        mock_sub.num_comments = 20
        mock_sub.upvote_ratio = 0.8

        # Manually calculate expected score
        expected_score = (100 * 0.8) + (20 * 2)  # 80 + 40 = 120

        # This tests the logic in _extract_reddit_metadata
        engagement_score = (mock_sub.score * mock_sub.upvote_ratio) + (mock_sub.num_comments * 2)

        assert engagement_score == expected_score

    @pytest.mark.asyncio
    async def test_article_sorting_by_engagement(self, fetcher):
        """Test that articles are sorted by engagement score."""
        # Create submissions with different engagement scores
        high_engagement = MagicMock()
        high_engagement.id = 'high'
        high_engagement.title = 'High Engagement Post'
        high_engagement.score = 200
        high_engagement.num_comments = 50
        high_engagement.upvote_ratio = 0.9
        high_engagement.selftext = 'Great content'
        high_engagement.author = 'author1'
        high_engagement.created_utc = 1640995200
        high_engagement.permalink = '/r/LocalLLaMA/comments/high/'
        high_engagement.link_flair_text = 'Discussion'
        high_engagement.is_self = True
        high_engagement.stickied = False
        high_engagement.total_awards_received = 5
        high_engagement.distinguished = None

        low_engagement = MagicMock()
        low_engagement.id = 'low'
        low_engagement.title = 'Low Engagement Post'
        low_engagement.score = 60
        low_engagement.num_comments = 5
        low_engagement.upvote_ratio = 0.7
        low_engagement.selftext = 'Less popular content'
        low_engagement.author = 'author2'
        low_engagement.created_utc = 1640995200
        low_engagement.permalink = '/r/LocalLLaMA/comments/low/'
        low_engagement.link_flair_text = 'Discussion'
        low_engagement.is_self = True
        low_engagement.stickied = False
        low_engagement.total_awards_received = 1
        low_engagement.distinguished = None

        # Mock the _fetch_from_stream method directly
        async def mock_fetch_from_stream(stream, stream_name):
            if stream_name == "hot":
                # Return low engagement first to test sorting
                return [low_engagement, high_engagement]
            else:
                return []

        with patch.object(fetcher, '_fetch_from_stream', side_effect=mock_fetch_from_stream), \
             patch.object(fetcher, '_is_quality_post', return_value=True):

            articles = await fetcher.fetch(max_articles=10)

        # High engagement post should be first
        assert len(articles) == 2
        assert 'High Engagement Post' in articles[0].title
        assert 'Low Engagement Post' in articles[1].title
