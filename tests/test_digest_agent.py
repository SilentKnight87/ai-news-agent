"""
Tests for digest agent.
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, Mock, patch

import pytest

from src.agents.digest_agent import DigestAgent, get_digest_agent
from src.models.articles import Article, ArticleSource
from src.models.schemas import DigestSummary


@pytest.fixture
def sample_articles():
    """Create sample articles for testing."""
    articles = []

    for i in range(5):
        article = Article(
            source_id=f"test_article_{i+1}",
            title=f"AI Research Article {i+1}",
            url=f"https://example.com/article{i+1}",
            content=f"This is the content for article {i+1} about AI research.",
            source=ArticleSource.ARXIV,
            published_at=datetime.now(UTC),
            summary=f"Summary of article {i+1} about AI developments.",
            relevance_score=85.0 + i,
            categories=["Research", "Technical"],
            key_points=[f"Key point {i+1}.1", f"Key point {i+1}.2"]
        )
        articles.append(article)

    return articles


class TestDigestAgent:
    """Test the DigestAgent class."""

    @patch('src.agents.digest_agent.Agent')
    @patch('os.environ')
    def test_digest_agent_initialization(self, mock_environ, mock_agent_class):
        """Test digest agent initialization."""
        mock_agent = Mock()
        mock_agent_class.return_value = mock_agent

        agent = DigestAgent()

        # Should set environment variable
        mock_environ.__setitem__.assert_called_with('GOOGLE_API_KEY', agent.settings.gemini_api_key)

        # Should create PydanticAI agent
        mock_agent_class.assert_called_once()
        call_args = mock_agent_class.call_args
        assert call_args[1]['model'] == 'gemini-1.5-flash'
        assert call_args[1]['output_type'] == DigestSummary

    def test_select_top_articles(self, sample_articles):
        """Test selection of top articles."""
        agent = DigestAgent()

        top_articles = agent._select_top_articles(sample_articles, max_count=3)

        assert len(top_articles) == 3
        # Should be sorted by relevance score (highest first)
        assert top_articles[0].relevance_score >= top_articles[1].relevance_score
        assert top_articles[1].relevance_score >= top_articles[2].relevance_score

    def test_prepare_digest_input(self, sample_articles):
        """Test preparation of digest input text."""
        agent = DigestAgent()

        input_text = agent._prepare_digest_input(sample_articles, max_length=1000)

        assert isinstance(input_text, str)
        assert len(input_text) > 0
        assert "Article 1:" in input_text
        assert "Target Summary Length: 1000" in input_text
        assert "Relevance:" in input_text

        # Should include article details
        for article in sample_articles:
            assert article.title in input_text

    def test_is_article_relevant_to_theme(self, sample_articles):
        """Test theme relevance checking."""
        agent = DigestAgent()

        # Create article with specific content
        llm_article = Article(
            source_id="llm_test_article",
            title="Large Language Model Training Advances",
            url="https://example.com/llm",
            content="Research on LLM training techniques",
            source=ArticleSource.ARXIV,
            published_at=datetime.now(UTC),
            categories=["LLM", "Training"],
            key_points=["New training method", "Improved efficiency"]
        )

        # Should match LLM theme
        assert agent._is_article_relevant_to_theme(llm_article, "LLM") is True
        assert agent._is_article_relevant_to_theme(llm_article, "Language Model") is True

        # Should not match unrelated theme
        assert agent._is_article_relevant_to_theme(llm_article, "Computer Vision") is False

    @pytest.mark.asyncio
    @patch('src.agents.digest_agent.Agent')
    async def test_generate_quick_summary(self, mock_agent_class, sample_articles):
        """Test quick summary generation."""
        # Mock the agent
        mock_agent = Mock()
        mock_result = Mock()
        mock_result.data = "Quick summary of AI developments today."
        mock_agent.run = AsyncMock(return_value=mock_result)
        mock_agent_class.return_value = mock_agent

        agent = DigestAgent()

        summary = await agent.generate_quick_summary(sample_articles, max_length=200)

        assert isinstance(summary, str)
        assert len(summary) > 0
        mock_agent.run.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_quick_summary_empty_articles(self):
        """Test quick summary with empty article list."""
        agent = DigestAgent()

        summary = await agent.generate_quick_summary([], max_length=200)

        assert summary == "No articles available for summary."

    @pytest.mark.asyncio
    @patch('src.agents.digest_agent.Agent')
    async def test_generate_digest(self, mock_agent_class, sample_articles):
        """Test full digest generation."""
        # Mock the main agent
        mock_agent = Mock()
        mock_result = Mock()
        mock_result.data = DigestSummary(
            summary_text="Today's AI developments include significant advances in machine learning.",
            key_themes=["Machine Learning", "Research"],
            notable_developments=["New model architecture", "Improved training methods"]
        )
        mock_agent.run = AsyncMock(return_value=mock_result)
        mock_agent_class.return_value = mock_agent

        agent = DigestAgent()
        agent.agent = mock_agent  # Override the agent

        digest_date = datetime.now(UTC)
        digest = await agent.generate_digest(sample_articles, digest_date)

        assert digest.digest_date == digest_date
        assert digest.total_articles_processed == len(sample_articles)
        assert len(digest.top_articles) <= 10
        assert len(digest.key_themes) > 0
        assert len(digest.notable_developments) > 0
        assert "Today's AI developments" in digest.summary_text

    @pytest.mark.asyncio
    async def test_generate_digest_empty_articles(self):
        """Test digest generation with empty article list."""
        agent = DigestAgent()

        with pytest.raises(ValueError, match="Cannot generate digest from empty article list"):
            await agent.generate_digest([], datetime.now(UTC))

    @pytest.mark.asyncio
    @patch('src.agents.digest_agent.Agent')
    async def test_generate_themed_digest(self, mock_agent_class, sample_articles):
        """Test themed digest generation."""
        # Add theme-specific article
        theme_article = Article(
            source_id="cv_test_article",
            title="Computer Vision Breakthrough",
            url="https://example.com/cv",
            content="New computer vision algorithm",
            source=ArticleSource.ARXIV,
            published_at=datetime.now(UTC),
            categories=["Computer Vision", "Research"],
            key_points=["Better accuracy", "Faster inference"]
        )
        articles_with_theme = sample_articles + [theme_article]

        # Mock the agent
        mock_agent = Mock()
        mock_result = Mock()
        mock_result.data = DigestSummary(
            summary_text="Computer vision advances dominate today's developments.",
            key_themes=["Computer Vision", "Accuracy"],
            notable_developments=["New CV algorithm"]
        )
        mock_agent.run = AsyncMock(return_value=mock_result)
        mock_agent_class.return_value = mock_agent

        agent = DigestAgent()
        agent.agent = mock_agent  # Override the agent

        digest_date = datetime.now(UTC)
        digest = await agent.generate_themed_digest(
            articles_with_theme,
            "Computer Vision",
            digest_date
        )

        assert digest.digest_date == digest_date
        assert "Computer Vision" in digest.key_themes
        assert "[Computer Vision Focus]" in digest.summary_text

    @pytest.mark.asyncio
    @patch('src.agents.digest_agent.Agent')
    async def test_generate_digest_error_handling(self, mock_agent_class, sample_articles):
        """Test error handling in digest generation."""
        # Mock agent to raise exception
        mock_agent = Mock()
        mock_agent.run.side_effect = Exception("API Error")
        mock_agent_class.return_value = mock_agent

        agent = DigestAgent()
        agent.agent = mock_agent

        with pytest.raises(Exception, match="API Error"):
            await agent.generate_digest(sample_articles, datetime.now(UTC))


class TestGlobalDigestAgent:
    """Test the global digest agent functionality."""

    def test_get_digest_agent_singleton(self):
        """Test that get_digest_agent returns singleton."""
        agent1 = get_digest_agent()
        agent2 = get_digest_agent()

        assert agent1 is agent2
        assert isinstance(agent1, DigestAgent)


@pytest.mark.asyncio
async def test_integration_digest_flow(sample_articles):
    """Integration test for digest generation flow."""

    # This test would normally require actual API calls
    # For now, we'll test the flow structure

    agent = get_digest_agent()

    # Test that we can prepare input
    input_text = agent._prepare_digest_input(sample_articles, 1000)
    assert len(input_text) > 0

    # Test that we can select top articles
    top_articles = agent._select_top_articles(sample_articles, 3)
    assert len(top_articles) == 3

    # Test theme checking
    relevant = agent._is_article_relevant_to_theme(sample_articles[0], "Research")
    assert isinstance(relevant, bool)
