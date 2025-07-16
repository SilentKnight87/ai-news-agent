name: "AI-Powered News Aggregator with PydanticAI and Supabase"
description: |

## Purpose
Build a production-ready AI news aggregator that monitors multiple AI/ML news sources, uses PydanticAI agents for intelligent summarization and relevance scoring, implements semantic deduplication with vector embeddings, and generates daily digests with text-to-speech capabilities.

## Core Principles
1. **Start Simple**: MVP with ArXiv, HackerNews, RSS feeds first
2. **Respect Rate Limits**: Strict adherence to API limits with exponential backoff
3. **Type Safety**: Leverage Pydantic throughout for validation
4. **Async First**: Use async/await for concurrent operations
5. **Test Everything**: Mock external APIs, validate core logic

---

## Goal
Create an automated pipeline that:
- Fetches AI/ML news from multiple sources every 15-30 minutes
- Uses PydanticAI agents to summarize and score articles for relevance
- Prevents duplicate stories using vector similarity (85% threshold)
- Generates daily digests with ElevenLabs audio summaries
- Provides real-time dashboard via Next.js frontend

## Why
- **Information Overload**: AI practitioners need curated, relevant news
- **Time Savings**: Automated summarization saves hours of reading
- **Audio Option**: Listen to digests during commute/exercise
- **No Duplicates**: Same story from multiple sources shown once

## What
### User-Visible Features
- Real-time dashboard showing latest AI news
- Daily digest emails with top stories
- Audio version of daily digest
- Relevance scoring (0-100) for each article
- Source attribution and timestamps

### Technical Requirements
- Process 500+ articles/day without duplicates
- Sub-3 second response time for web dashboard
- 99.9% uptime for scheduled tasks
- Audio generation within 30 seconds

### Success Criteria
- [ ] Fetches from ArXiv, HackerNews, 5 RSS feeds successfully
- [ ] Deduplication catches 90%+ of duplicate stories
- [ ] PydanticAI agents provide consistent summaries
- [ ] Daily digest generated automatically at 5 PM UTC
- [ ] All external API rate limits respected

## All Needed Context

### Documentation & References
```yaml
# MUST READ - Include these in your context window
- url: https://ai.pydantic.dev/
  why: PydanticAI agent setup, structured outputs, model configuration
  
- url: https://info.arxiv.org/help/api/index.html
  why: Query syntax, rate limits (3 sec), response format
  critical: Must use delay_seconds=3.0 in client
  
- url: https://github.com/HackerNews/API
  why: Firebase endpoints, no rate limit but be respectful
  
- url: https://supabase.com/docs/guides/ai/vector-embeddings
  why: pgvector setup, similarity search queries
  critical: Use vector(384) for all-MiniLM-L6-v2
  
- url: https://docs.python.org/3/library/asyncio.html
  why: Concurrent fetching patterns, gather vs TaskGroup
  
- url: https://elevenlabs.io/docs/api-reference/text-to-speech
  why: Streaming vs batch, voice IDs, error codes
  
- file: CLAUDE.md
  why: Project conventions - venv_linux, module structure, testing patterns
  
- file: INITIAL.md
  why: Complete feature requirements and data source tiers
```

### Current Codebase tree
```bash
ai-news-aggregator-agent/
├── CLAUDE.md
├── INITIAL.md
├── PLANNING.md
├── TASK.md
├── PRPs/
│   └── templates/
│       └── prp_base.md
└── examples/
    └── (empty - to be created)
```

### Desired Codebase tree with files to be added
```bash
ai-news-aggregator-agent/
├── src/
│   ├── __init__.py
│   ├── main.py                    # FastAPI app entry point
│   ├── config.py                  # Settings and environment vars
│   ├── models/
│   │   ├── __init__.py
│   │   ├── articles.py            # Pydantic models for articles
│   │   ├── database.py            # SQLAlchemy models
│   │   └── schemas.py             # API request/response schemas
│   ├── fetchers/
│   │   ├── __init__.py
│   │   ├── base.py                # Abstract fetcher interface
│   │   ├── arxiv_fetcher.py       # ArXiv API integration
│   │   ├── hackernews_fetcher.py  # HN Firebase API
│   │   ├── rss_fetcher.py         # Generic RSS parser
│   │   └── factory.py             # Fetcher factory pattern
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── news_agent.py          # Article summarization
│   │   ├── digest_agent.py        # Daily digest creation
│   │   └── prompts.py             # System prompts
│   ├── services/
│   │   ├── __init__.py
│   │   ├── deduplication.py       # Vector similarity logic
│   │   ├── embeddings.py          # HuggingFace integration
│   │   ├── tts.py                 # ElevenLabs integration
│   │   └── rate_limiter.py        # Rate limiting utilities
│   ├── repositories/
│   │   ├── __init__.py
│   │   └── articles.py            # Database operations
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes.py              # API endpoints
│   │   └── dependencies.py        # FastAPI dependencies
│   └── scheduled/
│       ├── __init__.py
│       ├── fetch_articles.py      # Periodic fetching
│       └── generate_digest.py     # Daily digest job
├── tests/
│   ├── __init__.py
│   ├── conftest.py                # Pytest fixtures
│   ├── test_fetchers/
│   ├── test_agents/
│   ├── test_services/
│   └── test_api/
├── migrations/
│   └── 001_initial_schema.sql     # Supabase migrations
├── examples/                       # Implementation examples
├── requirements.txt
├── .env.example
├── pytest.ini
├── pyproject.toml
└── README.md
```

### Known Gotchas & Library Quirks
```python
# CRITICAL: ArXiv enforces 3-second delay between requests
# Use arxiv.Client(delay_seconds=3.0) or get banned

# CRITICAL: HuggingFace free tier has rate limits
# Cache embeddings in database to avoid re-computing

# CRITICAL: Supabase pgvector requires specific index type
# Use HNSW for production (IVFFlat for < 1000 vectors)

# CRITICAL: PydanticAI requires async context for agents
# All agent calls must be awaited

# CRITICAL: RSS feeds may have different date formats
# feedparser handles this but check entry.get('published_parsed')

# CRITICAL: ElevenLabs charges per character
# Limit digest to 2000 chars to control costs
```

## Implementation Blueprint

### Data models and structure

```python
# models/articles.py
from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional, List

class ArticleSource(str, Enum):
    ARXIV = "arxiv"
    HACKERNEWS = "hackernews"
    RSS = "rss"

class Article(BaseModel):
    """Core article model with validation"""
    source_id: str  # Unique ID from source
    source: ArticleSource
    title: str = Field(..., min_length=1, max_length=500)
    content: str = Field(..., max_length=10000)
    url: str
    author: Optional[str] = None
    published_at: datetime
    fetched_at: datetime = Field(default_factory=datetime.utcnow)
    
    # AI-generated fields
    summary: Optional[str] = None
    relevance_score: Optional[float] = Field(None, ge=0, le=100)
    categories: List[str] = Field(default_factory=list)
    key_points: List[str] = Field(default_factory=list)
    
    # Deduplication
    embedding: Optional[List[float]] = None  # 384-dim vector
    is_duplicate: bool = False
    duplicate_of: Optional[str] = None
    
    @validator('url')
    def validate_url(cls, v):
        if not v.startswith(('http://', 'https://')):
            raise ValueError('URL must start with http:// or https://')
        return v

# models/schemas.py
class NewsAnalysis(BaseModel):
    """PydanticAI agent output schema"""
    summary: str = Field(..., max_length=500)
    relevance_score: float = Field(..., ge=0, le=100)
    categories: List[str] = Field(..., max_items=5)
    key_points: List[str] = Field(..., min_items=1, max_items=5)

class DailyDigest(BaseModel):
    """Daily digest schema"""
    date: datetime
    top_articles: List[Article]
    summary_text: str = Field(..., max_length=2000)  # For TTS
    total_articles_processed: int
    audio_url: Optional[str] = None
```

### List of tasks to be completed in order

```yaml
Task 1 - Setup Project Structure:
CREATE src/__init__.py
CREATE requirements.txt:
  - CONTENTS: |
      # Core
      fastapi==0.109.0
      uvicorn[standard]==0.27.0
      pydantic==2.5.0
      pydantic-ai==0.0.7
      python-dotenv==1.0.0
      
      # Data fetching
      arxiv==2.1.0
      feedparser==6.0.11
      httpx==0.26.0
      aiohttp==3.9.1
      
      # AI/ML
      sentence-transformers==2.3.1
      
      # Database
      supabase==2.3.4
      sqlalchemy==2.0.25
      
      # Utilities
      tenacity==8.2.3
      
      # Dev/Test
      pytest==7.4.4
      pytest-asyncio==0.23.3
      pytest-mock==3.12.0
      ruff==0.1.11
      mypy==1.8.0

CREATE .env.example:
  - CONTENTS: |
      # Supabase
      SUPABASE_URL=your_supabase_url
      SUPABASE_ANON_KEY=your_anon_key
      
      # AI Services
      GEMINI_API_KEY=your_gemini_key
      ELEVENLABS_API_KEY=your_elevenlabs_key
      HF_API_KEY=your_huggingface_key
      
      # Config
      FETCH_INTERVAL_MINUTES=30
      DIGEST_HOUR_UTC=8

CREATE pytest.ini:
  - CONTENTS: |
      [pytest]
      asyncio_mode = auto
      testpaths = tests
      python_files = test_*.py
      python_classes = Test*
      python_functions = test_*

Task 2 - Core Configuration:
CREATE src/config.py:
  - PATTERN: Use pydantic Settings for validation
  - INCLUDE: All env vars with defaults
  - GOTCHA: Use @lru_cache for singleton pattern

Task 3 - Database Schema:
CREATE migrations/001_initial_schema.sql:
  - ENABLE: pgvector extension
  - CREATE: articles table with vector(384) column
  - INDEX: HNSW index on embedding column
  - INCLUDE: deduplication tracking columns

Task 4 - Base Models:
CREATE src/models/articles.py:
  - COPY: Data models from blueprint above
  - ADD: SQLAlchemy table definitions
  - INCLUDE: Vector type mapping

Task 5 - Fetcher Base Class:
CREATE src/fetchers/base.py:
  - DEFINE: Abstract fetcher interface
  - REQUIRE: fetch() -> List[Article] method
  - INCLUDE: Rate limiting decorator

Task 6 - ArXiv Fetcher:
CREATE src/fetchers/arxiv_fetcher.py:
  - USE: arxiv.Client(delay_seconds=3.0)
  - CATEGORIES: cs.AI, cs.LG, cs.CL
  - LIMIT: 100 articles per fetch
  - MAP: ArXiv result to Article model

Task 7 - HackerNews Fetcher:
CREATE src/fetchers/hackernews_fetcher.py:
  - FETCH: /topstories.json first
  - FILTER: AI/ML keywords in title/text
  - CONCURRENT: Fetch items with asyncio.gather
  - RESPECT: 1 req/sec unofficial limit

Task 8 - RSS Fetcher:
CREATE src/fetchers/rss_fetcher.py:
  - SOURCES: List from INITIAL.md MVP sources
  - PARSE: Using feedparser
  - HANDLE: Different date formats gracefully
  - TIMEOUT: 10 seconds per feed

Task 9 - Rate Limiter Service:
CREATE src/services/rate_limiter.py:
  - IMPLEMENT: Token bucket algorithm
  - ADD: Exponential backoff with jitter
  - DECORATOR: @rate_limit(calls=X, period=Y)
  - CIRCUIT BREAKER: After 5 consecutive failures

Task 10 - Embeddings Service:
CREATE src/services/embeddings.py:
  - MODEL: sentence-transformers/all-MiniLM-L6-v2
  - BATCH: Process up to 100 texts at once
  - CACHE: Store computed embeddings
  - NORMALIZE: Vectors before storage

Task 11 - PydanticAI News Agent:
CREATE src/agents/news_agent.py:
  - MODEL: gemini-1.5-flash (free tier)
  - OUTPUT: NewsAnalysis schema
  - PROMPT: Focus on AI/ML relevance
  - BATCH: Process articles concurrently

Task 12 - Deduplication Service:
CREATE src/services/deduplication.py:
  - THRESHOLD: 0.85 cosine similarity
  - QUERY: Supabase vector similarity search
  - COMBINE: URL exact match + vector similarity
  - MARK: Duplicates with reference to original

Task 13 - Article Repository:
CREATE src/repositories/articles.py:
  - CRUD: Create, read, update operations
  - VECTOR SEARCH: similarity_search method
  - BATCH: Insert multiple articles
  - TRANSACTION: Ensure consistency

Task 14 - Digest Agent:
CREATE src/agents/digest_agent.py:
  - SELECT: Top 10 articles by relevance
  - GENERATE: Coherent summary under 2000 chars
  - FORMAT: For both text and audio
  - INCLUDE: Source attribution

Task 15 - TTS Service:
CREATE src/services/tts.py:
  - API: ElevenLabs text-to-speech
  - VOICE: Choose appropriate voice ID
  - STREAMING: For real-time generation
  - STORAGE: Save audio to Supabase

Task 16 - Scheduled Fetcher:
CREATE src/scheduled/fetch_articles.py:
  - INTERVAL: Every 30 minutes
  - PARALLEL: Fetch all sources concurrently
  - PROCESS: Through news agent
  - DEDUPLICATE: Before storage
  - ERROR HANDLING: Continue on single source failure

Task 17 - Digest Generator:
CREATE src/scheduled/generate_digest.py:
  - SCHEDULE: Daily at 8 AM UTC
  - QUERY: Last 24 hours of articles
  - GENERATE: Text and audio versions
  - STORE: In daily_digests table
  - NOTIFY: Via webhook (optional)

Task 18 - FastAPI Routes:
CREATE src/api/routes.py:
  - GET /articles: Paginated article list
  - GET /articles/{id}: Single article
  - GET /digest/latest: Today's digest
  - GET /digest/{date}: Historical digest
  - POST /webhook/fetch: Trigger manual fetch

Task 19 - Main Application:
CREATE src/main.py:
  - SETUP: FastAPI with CORS
  - MOUNT: API routes
  - INITIALIZE: Scheduled tasks
  - HEALTH CHECK: /health endpoint

Task 20 - Tests:
CREATE tests/ structure:
  - MOCK: All external APIs
  - TEST: Each fetcher with sample data
  - VALIDATE: Agent outputs
  - VERIFY: Deduplication logic
  - CHECK: API endpoints
```

### Per task pseudocode

```python
# Task 6 - ArXiv Fetcher
class ArxivFetcher(BaseFetcher):
    def __init__(self):
        self.client = arxiv.Client(
            page_size=100,
            delay_seconds=3.0,  # CRITICAL: Respect rate limit
            num_retries=5
        )
    
    async def fetch(self) -> List[Article]:
        # PATTERN: Use categories from requirements
        query = "cat:cs.AI OR cat:cs.LG OR cat:cs.CL"
        search = arxiv.Search(
            query=query,
            max_results=100,
            sort_by=arxiv.SortCriterion.SubmittedDate
        )
        
        articles = []
        # GOTCHA: This is sync but respects rate limit internally
        for result in self.client.results(search):
            article = Article(
                source_id=result.entry_id,
                source=ArticleSource.ARXIV,
                title=result.title,
                content=result.summary,
                url=result.pdf_url or result.entry_id,
                author=", ".join(a.name for a in result.authors[:3]),
                published_at=result.published
            )
            articles.append(article)
        
        return articles

# Task 11 - News Agent
from pydantic_ai import Agent

class NewsAnalyzer:
    def __init__(self):
        self.agent = Agent(
            'google-gemini/gemini-1.5-flash',
            result_type=NewsAnalysis,
            system_prompt="""You are an AI news analyst. Analyze articles for:
            1. Relevance to AI/ML (0-100 score)
            2. Key technical points
            3. Appropriate categories
            Prioritize: breakthroughs, new models, industry impact"""
        )
    
    async def analyze_article(self, article: Article) -> NewsAnalysis:
        # PATTERN: PydanticAI structured output
        result = await self.agent.run(
            f"Title: {article.title}\n\nContent: {article.content}"
        )
        return result.data

# Task 12 - Deduplication
async def find_duplicates(
    article: Article, 
    supabase: Client,
    threshold: float = 0.85
) -> Optional[str]:
    # CRITICAL: Embedding must be normalized
    if not article.embedding:
        return None
    
    # PATTERN: Supabase vector similarity search
    response = supabase.rpc(
        'match_articles',
        {
            'query_embedding': article.embedding,
            'match_threshold': threshold,
            'match_count': 5
        }
    ).execute()
    
    # Check both vector similarity and URL similarity
    for match in response.data:
        # Exact URL match
        if match['url'] == article.url:
            return match['id']
        
        # High similarity + same day = likely duplicate
        if (match['similarity'] > threshold and 
            article.published_at.date() == match['published_at'].date()):
            return match['id']
    
    return None
```

### Integration Points
```yaml
DATABASE:
  - migration: "Enable pgvector, create articles table with vector index"
  - function: |
      CREATE OR REPLACE FUNCTION match_articles(
        query_embedding vector(384),
        match_threshold float,
        match_count int
      ) RETURNS TABLE (
        id uuid,
        url text,
        similarity float,
        published_at timestamp
      ) AS $$
      BEGIN
        RETURN QUERY
        SELECT
          articles.id,
          articles.url,
          1 - (articles.embedding <=> query_embedding) as similarity,
          articles.published_at
        FROM articles
        WHERE 1 - (articles.embedding <=> query_embedding) > match_threshold
        ORDER BY articles.embedding <=> query_embedding
        LIMIT match_count;
      END;
      $$ LANGUAGE plpgsql;
  
CONFIG:
  - add to: src/config.py
  - pattern: |
      class Settings(BaseSettings):
          supabase_url: str
          supabase_anon_key: str
          gemini_api_key: str
          fetch_interval_minutes: int = 30
          
      @lru_cache
      def get_settings():
          return Settings()
  
SCHEDULED TASKS:
  - framework: "Use asyncio with while True loops for MVP"
  - pattern: |
      async def fetch_articles_task():
          while True:
              try:
                  await fetch_all_sources()
              except Exception as e:
                  logger.error(f"Fetch failed: {e}")
              await asyncio.sleep(settings.fetch_interval_minutes * 60)
```

## Validation Loop

### Level 1: Syntax & Style
```bash
# Setup virtual environment first
python -m venv venv_linux
source venv_linux/bin/activate
pip install -r requirements.txt

# Run these FIRST - fix any errors before proceeding
ruff check src/ --fix
mypy src/

# Expected: No errors. Common fixes:
# - Missing type hints: Add -> None for functions without return
# - Import errors: Ensure all modules have __init__.py
```

### Level 2: Unit Tests
```python
# tests/test_fetchers/test_arxiv.py
import pytest
from unittest.mock import Mock, patch
from src.fetchers.arxiv_fetcher import ArxivFetcher

@pytest.mark.asyncio
async def test_arxiv_fetcher_respects_rate_limit():
    """Verify 3-second delay is configured"""
    fetcher = ArxivFetcher()
    assert fetcher.client.delay_seconds == 3.0

@pytest.mark.asyncio
async def test_arxiv_fetcher_handles_errors():
    """Test graceful error handling"""
    with patch('arxiv.Client.results', side_effect=Exception("API Error")):
        fetcher = ArxivFetcher()
        with pytest.raises(Exception):
            await fetcher.fetch()

# tests/test_services/test_deduplication.py
@pytest.mark.asyncio
async def test_exact_url_match():
    """Exact URL always counts as duplicate"""
    article = Article(url="https://example.com/article1", ...)
    mock_supabase = Mock()
    mock_supabase.rpc.return_value.execute.return_value.data = [
        {'id': '123', 'url': 'https://example.com/article1', 'similarity': 0.7}
    ]
    
    duplicate_id = await find_duplicates(article, mock_supabase)
    assert duplicate_id == '123'

@pytest.mark.asyncio
async def test_similarity_threshold():
    """Only flag as duplicate above threshold"""
    # Test with similarity below threshold
    # Test with similarity above threshold
```

```bash
# Run tests iteratively until passing:
source venv_linux/bin/activate
pytest tests/ -v

# For specific test file:
pytest tests/test_fetchers/test_arxiv.py -v

# With coverage:
pytest tests/ --cov=src --cov-report=html
```

### Level 3: Integration Test
```bash
# Start the service
source venv_linux/bin/activate
uvicorn src.main:app --reload

# Test article fetching
curl http://localhost:8000/health

# Test manual fetch trigger
curl -X POST http://localhost:8000/webhook/fetch

# Test article list
curl http://localhost:8000/articles?limit=10

# Monitor logs
tail -f logs/app.log

# Expected: Articles fetched and stored with no duplicates
# Check Supabase dashboard for stored articles
```

### Level 4: End-to-End Test
```bash
# Test complete pipeline
# 1. Trigger fetch
# 2. Verify deduplication
# 3. Check agent analysis
# 4. Generate digest
# 5. Verify audio generation

# SQL to verify in Supabase:
SELECT COUNT(*), COUNT(DISTINCT url) 
FROM articles 
WHERE fetched_at > NOW() - INTERVAL '1 hour';

# Should show same count (no duplicates)
```

## Final Validation Checklist
- [ ] All tests pass: `pytest tests/ -v`
- [ ] No linting errors: `ruff check src/`
- [ ] No type errors: `mypy src/`
- [ ] ArXiv fetcher respects 3-second delay
- [ ] Deduplication catches duplicate URLs
- [ ] Vector similarity works (test with known duplicates)
- [ ] Agents return valid structured output
- [ ] Scheduled tasks run without errors
- [ ] API endpoints return correct data
- [ ] Daily digest generated successfully
- [ ] Audio file created and accessible
- [ ] No API rate limit violations in logs

---

## Anti-Patterns to Avoid
- ❌ Don't skip the 3-second ArXiv delay - you will get banned
- ❌ Don't store raw embeddings without normalization
- ❌ Don't fetch all sources sequentially - use asyncio.gather()
- ❌ Don't ignore failed sources - log and continue with others
- ❌ Don't hardcode API keys - use environment variables
- ❌ Don't process articles synchronously - batch with agents
- ❌ Don't create digests over 2000 chars - ElevenLabs costs add up
- ❌ Don't trust external API data - validate with Pydantic

## Additional Implementation Notes

### Error Recovery Patterns
```python
# Circuit breaker for unreliable sources
class CircuitBreaker:
    def __init__(self, failure_threshold=5, timeout=300):
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.last_failure_time = None
        self.is_open = False
```

### Monitoring and Alerts
- Log all external API calls with duration
- Track success/failure rates per source
- Alert if any source fails 3 times in a row
- Monitor vector search performance

### Performance Optimization
- Batch embed articles in groups of 100
- Use connection pooling for Supabase
- Cache frequent vector searches
- Implement lazy loading for article content

**Confidence Score: 9/10**

This PRP provides comprehensive context for implementing the AI news aggregator with all necessary patterns, gotchas, and validation steps. The implementation should succeed in one pass with minor adjustments.