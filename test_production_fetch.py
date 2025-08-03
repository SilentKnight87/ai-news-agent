#!/usr/bin/env python3
"""
Test production article fetching and AI analysis.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path("src").absolute()))

from src.agents.news_agent import get_news_analyzer
from src.api.dependencies import get_supabase_client
from src.fetchers.factory import fetcher_factory
from src.repositories.articles import ArticleRepository
from src.services.deduplication import DeduplicationService

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

async def test_production_pipeline():
    """Test the complete production pipeline."""

    try:
        logger.info("🔍 Starting production pipeline test")

        # Test 1: Fetch articles from ArXiv
        logger.info("📰 Testing ArXiv fetcher...")
        arxiv_fetcher = fetcher_factory.get_fetcher("arxiv")
        articles = await arxiv_fetcher.fetch(max_articles=5)  # Small test batch
        logger.info(f"✅ Fetched {len(articles)} articles from ArXiv")

        if not articles:
            logger.warning("❌ No articles fetched from ArXiv")
            return False

        # Test 2: AI Analysis
        logger.info("🤖 Testing AI analysis...")
        news_analyzer = get_news_analyzer()
        analyzed_articles = await news_analyzer.analyze_and_update_articles(
            articles[:2], min_relevance_score=30.0  # Lower threshold for testing
        )
        logger.info(f"✅ Analyzed {len(analyzed_articles)} relevant articles")

        if not analyzed_articles:
            logger.warning("❌ No articles passed relevance filtering")
            return False

        # Show sample analysis
        sample = analyzed_articles[0]
        logger.info("📊 Sample analysis:")
        logger.info(f"  Title: {sample.title[:100]}...")
        logger.info(f"  Relevance: {sample.relevance_score}/100")
        logger.info(f"  Categories: {sample.categories}")
        logger.info(f"  Key points: {len(sample.key_points)} points")

        # Test 3: Deduplication
        logger.info("🔍 Testing deduplication...")
        supabase = get_supabase_client()
        dedup_service = DeduplicationService(supabase)
        unique_articles, duplicates = await dedup_service.process_articles_for_duplicates(
            analyzed_articles
        )
        logger.info(f"✅ Found {len(unique_articles)} unique, {len(duplicates)} duplicates")

        # Test 4: Database storage
        logger.info("💾 Testing database storage...")
        article_repo = ArticleRepository(supabase)

        if unique_articles:
            created = await article_repo.batch_create_articles(unique_articles)
            logger.info(f"✅ Stored {len(created)} articles in database")

        # Test 5: Retrieval
        logger.info("📖 Testing article retrieval...")
        retrieved = await article_repo.get_articles(limit=5)
        logger.info(f"✅ Retrieved {len(retrieved)} articles from database")

        logger.info("🎉 Production pipeline test completed successfully!")
        return True

    except Exception as e:
        logger.error(f"❌ Production pipeline test failed: {e}", exc_info=True)
        return False

async def main():
    """Main test function."""
    success = await test_production_pipeline()
    if success:
        print("\n✅ ALL TESTS PASSED - Production pipeline is working!")
        sys.exit(0)
    else:
        print("\n❌ TESTS FAILED - See logs above for details")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
