name: "New AI News Sources Integration PRP"
description: |

## Purpose
Implement enhanced AI news aggregation with 4 additional high-value sources: YouTube RSS feeds, Hugging Face Models API, Reddit r/LocalLLaMA, and GitHub releases tracking. This feature significantly expands content diversity while maintaining the existing architecture patterns.

## Core Principles Applied
1. **Context is King**: All external API documentation and existing patterns referenced
2. **Validation Loops**: Comprehensive testing for each new fetcher
3. **Information Dense**: Uses existing BaseFetcher pattern and configuration approaches
4. **Progressive Success**: MVP sources first (YouTube RSS, HF Models), then Tier 1 (Reddit, GitHub)
5. **Global rules**: Follows CLAUDE.md patterns for module structure and testing

---

## Goal
Implement 4 new AI news sources to enhance content diversity and coverage:
- **YouTube RSS Integration** (MVP): Add video content from key AI educators
- **Hugging Face Models Fetcher** (MVP): Track new model releases and trending models  
- **Reddit Integration** (Tier 1): Community insights from r/LocalLLaMA
- **GitHub Releases Fetcher** (Tier 1): Track AI development tool updates

## Why
- **Business value**: Provides unique content types not available in current RSS/ArXiv/HN sources
- **Integration**: Seamlessly extends existing fetcher architecture and UI patterns
- **Problems solved**: 
  - Lack of video tutorial content for visual learners
  - Missing community discussions and insights
  - No tracking of model releases and tool updates
  - Limited to text-based sources only

## What
Enhanced news aggregation system that fetches from 4 additional sources while maintaining existing quality scoring, deduplication, and AI analysis workflows.

### Success Criteria
- [ ] YouTube RSS feeds integrated into existing RSS fetcher with 5+ AI education channels
- [ ] Hugging Face Models fetcher tracks trending and new models with metadata
- [ ] Reddit fetcher pulls quality discussions from r/LocalLLaMA with engagement filtering
- [ ] GitHub releases fetcher monitors 5+ AI development tools
- [ ] All new sources display properly in Netflix-style UI with source-specific styling
- [ ] Comprehensive test coverage for all new fetchers (90%+ coverage)
- [ ] No performance degradation in existing fetch cycles
- [ ] All validation gates pass: ruff, mypy, pytest

## All Needed Context

### Documentation & References
```yaml
# MUST READ - Include these in your context window
- url: https://huggingface.co/docs/hub/en/api
  why: Models API endpoints, authentication, rate limits (1000 req/hour)
  
- url: https://praw.readthedocs.io/en/stable/getting_started/quick_start.html
  why: Reddit API authentication setup, rate limits (60 req/min)
  
- url: https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api
  why: GitHub API rate limits (5000 req/hour authenticated), releases endpoint
  
- file: src/fetchers/base.py
  why: BaseFetcher pattern with rate limiting and circuit breaker
  
- file: src/fetchers/rss_fetcher.py  
  why: Configuration loading pattern, concurrent fetching, error handling
  
- file: src/fetchers/factory.py
  why: Fetcher registration pattern for new source types
  
- file: src/models/articles.py
  why: ArticleSource enum extension and Article model metadata field
  
- file: tests/test_fetchers/test_rss_fetcher.py
  why: Testing patterns for async fetchers with mocking
  
- file: config/rss_feeds.json
  why: Configuration file structure for YouTube RSS feeds
  
- file: mockup/index.html
  why: Netflix-style UI patterns for different content types
```

### Current Codebase Structure
```bash
src/
├── fetchers/
│   ├── base.py              # Abstract fetcher with rate limiting
│   ├── rss_fetcher.py       # Config-driven RSS fetching  
│   ├── arxiv_fetcher.py     # Research paper fetching
│   ├── hackernews_fetcher.py # HN API integration
│   └── factory.py           # Fetcher registration
├── models/
│   ├── articles.py          # Article model and ArticleSource enum
│   └── schemas.py           # Pydantic validation schemas
├── config.py                # Settings with environment variables
└── services/
    ├── rate_limiter.py      # Rate limiting utilities
    └── deduplication.py     # Cross-source dedup
```

### Desired Codebase Structure After Implementation
```bash
src/fetchers/
├── base.py                  # [UNCHANGED] Abstract fetcher
├── rss_fetcher.py          # [MODIFIED] Add YouTube RSS support
├── huggingface_fetcher.py  # [NEW] HF Models API fetcher
├── reddit_fetcher.py       # [NEW] PRAW-based Reddit fetcher  
├── github_fetcher.py       # [NEW] GitHub releases fetcher
└── factory.py              # [MODIFIED] Register new fetchers

src/models/articles.py       # [MODIFIED] Add new ArticleSource enums
config/rss_feeds.json        # [MODIFIED] Add YouTube channels
tests/test_fetchers/
├── test_huggingface_fetcher.py  # [NEW] HF fetcher tests
├── test_reddit_fetcher.py       # [NEW] Reddit fetcher tests
└── test_github_fetcher.py       # [NEW] GitHub fetcher tests
```

### Known Gotchas & Library Quirks
```python
# CRITICAL: YouTube RSS feeds are Atom format, not RSS - feedparser handles both
# GOTCHA: YouTube RSS only shows last 10 videos, use feedparser.parse() same as RSS

# CRITICAL: Hugging Face API uses requests/hour limit, not per-second
# GOTCHA: HF trending endpoint may be cached, check last-modified headers

# CRITICAL: PRAW requires OAuth credentials (client_id, client_secret, user_agent)
# GOTCHA: Reddit rate limit is 60 requests per minute, use asyncpraw for async
# WARNING: Reddit requires user_agent format: "platform:app_id:version (by /u/username)"

# CRITICAL: GitHub API requires authentication for 5000 req/hour (60 without)
# GOTCHA: GitHub releases endpoint is paginated, use per_page=100 parameter
# WARNING: GITHUB_TOKEN in Actions has different limits than personal tokens

# EXISTING PATTERN: All fetchers must inherit from BaseFetcher and implement fetch()
# EXISTING PATTERN: Use RateLimitedHTTPClient for external API calls
# EXISTING PATTERN: Configuration via Settings class with environment variables
```

## Implementation Blueprint

### Data Models and Structure

Extend existing Article model to support source-specific metadata:
```python
# MODIFY src/models/articles.py - Add new source types
class ArticleSource(str, Enum):
    ARXIV = "arxiv"
    HACKERNEWS = "hackernews" 
    RSS = "rss"
    YOUTUBE = "youtube"      # NEW - for YouTube RSS feeds
    HUGGINGFACE = "huggingface"  # NEW - for model releases
    REDDIT = "reddit"        # NEW - for community posts
    GITHUB = "github"        # NEW - for tool releases

# Article model already has metadata: dict field for source-specific data
# YouTube: {"duration": "12:34", "views": 45000, "channel": "IndyDevDan"}
# HF: {"model_size": "8B", "downloads": 12500, "license": "Apache-2.0", "trending": true}
# Reddit: {"upvotes": 342, "comments": 89, "subreddit": "LocalLLaMA"}
# GitHub: {"version": "0.5.0", "is_prerelease": false, "breaking_changes": true}
```

### List of Tasks (Implementation Order)

```yaml
Task 1: Extend Article Model and Factory
MODIFY src/models/articles.py:
  - ADD new ArticleSource enum values (YOUTUBE, HUGGINGFACE, REDDIT, GITHUB)
  - VERIFY metadata field exists for source-specific data

MODIFY src/fetchers/factory.py:
  - PREPARE for new fetcher registration (will be added in subsequent tasks)

Task 2: YouTube RSS Integration (MVP - Quick Win)
MODIFY config/rss_feeds.json:
  - ADD new "youtube_channels" category with 5 AI education channels
  - USE format: https://www.youtube.com/feeds/videos.xml?channel_id=CHANNEL_ID

MODIFY src/fetchers/rss_fetcher.py:
  - ADD YouTube channel RSS feeds to existing configuration loading
  - PRESERVE existing RSS behavior - no separate fetcher needed
  - ADD metadata extraction for YouTube-specific fields (duration, channel)

Task 3: Hugging Face Models Fetcher (MVP - High Value)
CREATE src/fetchers/huggingface_fetcher.py:
  - INHERIT from BaseFetcher with 0.1 second rate limit (1000 req/hour)
  - IMPLEMENT trending models endpoint: https://huggingface.co/api/models?sort=trending
  - IMPLEMENT new models endpoint: https://huggingface.co/api/models?sort=lastModified
  - FILTER for text-generation, text2text-generation model types
  - EXTRACT metadata: model_size, downloads, likes, license, tags

Task 4: Reddit Fetcher (Tier 1 - Community Insights)  
CREATE src/fetchers/reddit_fetcher.py:
  - INHERIT from BaseFetcher with 1.0 second rate limit (60 req/minute)
  - USE asyncpraw library for async Reddit API access
  - TARGET r/LocalLLaMA subreddit exclusively
  - FILTER posts with 50+ upvotes or 10+ comments
  - EXTRACT metadata: upvotes, comments, awards, post_type

Task 5: GitHub Releases Fetcher (Tier 1 - Tool Updates)
CREATE src/fetchers/github_fetcher.py:  
  - INHERIT from BaseFetcher with 0.5 second rate limit (5000 req/hour)
  - TARGET repositories: anthropics/anthropic-sdk-python, modelcontextprotocol/servers
  - USE GitHub REST API: https://api.github.com/repos/{owner}/{repo}/releases
  - FILTER for releases published in last 30 days
  - EXTRACT metadata: version, is_prerelease, breaking_changes

Task 6: Register New Fetchers
MODIFY src/fetchers/factory.py:
  - ADD imports for new fetchers
  - REGISTER new fetchers in _fetcher_classes dict
  - ENSURE get_supported_sources() includes new types

Task 7: Configuration Integration
MODIFY src/config.py:
  - ADD Reddit API credentials (client_id, client_secret, user_agent)  
  - ADD GitHub token for authenticated requests
  - ADD Hugging Face token (optional for higher limits)
  - FOLLOW existing pattern with Field() descriptions

Task 8: Comprehensive Testing
CREATE tests/test_fetchers/test_huggingface_fetcher.py:
  - TEST successful model fetching with mocked API responses
  - TEST rate limiting behavior
  - TEST metadata extraction and Article creation
  - TEST error handling and circuit breaker

CREATE tests/test_fetchers/test_reddit_fetcher.py:
  - TEST successful post fetching with mocked PRAW
  - TEST upvote/comment filtering
  - TEST rate limiting and authentication
  - TEST error handling for API failures

CREATE tests/test_fetchers/test_github_fetcher.py:
  - TEST successful releases fetching with mocked GitHub API
  - TEST pagination handling
  - TEST recent releases filtering (30 days)
  - TEST error handling and authentication

MODIFY tests/test_fetchers/test_rss_fetcher.py:
  - ADD tests for YouTube RSS channel integration
  - TEST YouTube metadata extraction
  - VERIFY existing RSS behavior unchanged

Task 9: Final Integration and Validation
UPDATE .env.example:
  - ADD new environment variables with examples
  - DOCUMENT required Reddit/GitHub credentials

RUN comprehensive validation:
  - EXECUTE all validation loops (ruff, mypy, pytest)
  - VERIFY all new sources fetch successfully
  - TEST deduplication across sources
  - CONFIRM UI displays new content types properly
```

### Per Task Pseudocode

```python
# Task 3: Hugging Face Models Fetcher
class HuggingFaceFetcher(BaseFetcher):
    def __init__(self, settings):
        super().__init__(source=ArticleSource.HUGGINGFACE, rate_limit_delay=0.1)
        # PATTERN: Use RateLimitedHTTPClient for API calls
        self.client = RateLimitedHTTPClient(requests_per_second=2.5)
        self.base_url = "https://huggingface.co/api"
        self.headers = {"Authorization": f"Bearer {settings.hf_api_key}"} if settings.hf_api_key else {}
    
    async def fetch(self, max_articles: int = 50) -> list[Article]:
        # CRITICAL: Fetch both trending and new models
        trending_models = await self._fetch_trending_models()
        new_models = await self._fetch_new_models()
        
        # PATTERN: Convert API response to Article objects
        articles = []
        for model in trending_models + new_models:
            if self._is_relevant_model(model):  # Filter for LLM models
                article = self._model_to_article(model)
                articles.append(article)
        
        return articles[:max_articles]

# Task 4: Reddit Fetcher  
class RedditFetcher(BaseFetcher):
    def __init__(self, settings):
        super().__init__(source=ArticleSource.REDDIT, rate_limit_delay=1.0)
        # GOTCHA: asyncpraw requires different initialization than praw
        self.reddit = asyncpraw.Reddit(
            client_id=settings.reddit_client_id,
            client_secret=settings.reddit_client_secret,
            user_agent=f"AI-News-Aggregator/1.0 (by /u/{settings.reddit_username})"
        )
    
    async def fetch(self, max_articles: int = 50) -> list[Article]:
        subreddit = await self.reddit.subreddit("LocalLLaMA")
        articles = []
        
        # PATTERN: Fetch multiple sorted streams concurrently
        hot_posts = subreddit.hot(limit=25)
        top_posts = subreddit.top(time_filter="day", limit=25)
        
        async for submission in hot_posts:
            if self._is_quality_post(submission):  # 50+ upvotes or 10+ comments
                articles.append(self._submission_to_article(submission))
        
        return articles[:max_articles]
```

### Integration Points
```yaml
DATABASE:
  - migration: Already supports new ArticleSource values via string enum
  - index: Existing indexes on source column will work
  
CONFIG:
  - add to: src/config.py
  - pattern: "reddit_client_id: str = Field(..., description='Reddit OAuth client ID')"
  
FACTORY:
  - add to: src/fetchers/factory.py  
  - pattern: "ArticleSource.HUGGINGFACE: HuggingFaceFetcher,"
  
ENVIRONMENT:
  - add to: .env
  - pattern: "REDDIT_CLIENT_ID=your_reddit_client_id"
```

## Validation Loop

### Level 1: Syntax & Style
```bash
# Run these FIRST - fix any errors before proceeding
ruff check src/fetchers/ --fix      # Auto-fix new fetcher files
mypy src/fetchers/                  # Type checking on all fetchers
ruff check src/models/articles.py --fix  # Check model changes

# Expected: No errors. If errors, READ error message and fix source.
```

### Level 2: Unit Tests
```python
# Each new fetcher needs comprehensive test coverage
# CREATE test files following existing patterns from test_rss_fetcher.py

def test_huggingface_fetcher_trending_models():
    """Test HF fetcher retrieves trending models correctly"""
    # PATTERN: Mock API response, verify Article creation
    
def test_reddit_fetcher_filters_quality_posts():
    """Test Reddit fetcher applies upvote/comment filters"""  
    # PATTERN: Mock PRAW responses, verify filtering logic
    
def test_github_fetcher_recent_releases():
    """Test GitHub fetcher gets recent releases only"""
    # PATTERN: Mock GitHub API, verify date filtering

def test_youtube_rss_metadata_extraction():
    """Test YouTube RSS extracts video metadata correctly"""
    # PATTERN: Mock feedparser response with YouTube Atom format
```

```bash
# Run and iterate until passing:
uv run pytest tests/test_fetchers/ -v
# If failing: Read error, fix root cause, re-run (never mock to pass real bugs)
```

### Level 3: Integration Test
```bash
# Set up test environment with real credentials (in .env.test)
export REDDIT_CLIENT_ID=test_client_id
export GITHUB_TOKEN=test_token

# Test each fetcher individually
uv run python -c "
from src.fetchers.factory import fetcher_factory
from src.config import get_settings

settings = get_settings()
hf_fetcher = fetcher_factory.get_fetcher('huggingface')
articles = await hf_fetcher.fetch(max_articles=5)
print(f'HF Fetcher: {len(articles)} articles')
"

# Expected: Each fetcher returns articles without errors
# If error: Check logs for API authentication or rate limit issues
```

## Final Validation Checklist
- [ ] All tests pass: `uv run pytest tests/ -v`
- [ ] No linting errors: `uv run ruff check src/`
- [ ] No type errors: `uv run mypy src/`
- [ ] All new fetchers registered in factory: `python -c "from src.fetchers.factory import fetcher_factory; print(fetcher_factory.get_supported_sources())"`
- [ ] YouTube RSS integrated without breaking existing RSS feeds
- [ ] New ArticleSource enums work in database operations
- [ ] API credentials documented in .env.example
- [ ] Error cases handled gracefully (API timeouts, auth failures)
- [ ] Rate limiting respects API limits for all services
- [ ] Logs are informative but not verbose

---

## Anti-Patterns to Avoid
- ❌ Don't create separate YouTube fetcher - extend existing RSS fetcher
- ❌ Don't skip rate limiting because APIs have "generous" limits  
- ❌ Don't ignore failing tests - mock properly and fix real issues
- ❌ Don't hardcode API URLs or credentials - use Settings class
- ❌ Don't fetch all models/posts - implement proper filtering
- ❌ Don't break existing RSS behavior when adding YouTube channels
- ❌ Don't use synchronous Reddit API (praw) - use asyncpraw for consistency

## Expected Outcome

After successful implementation:
1. **4 new content sources** active and fetching regularly
2. **Enhanced content diversity**: videos, models, community discussions, tool updates  
3. **Zero breaking changes** to existing functionality
4. **Comprehensive test coverage** ensuring reliability
5. **Proper error handling** and graceful degradation
6. **Rate limit compliance** for all external APIs
7. **Netflix-style UI** displays new content types appropriately

**Confidence Score: 9/10** - High confidence due to comprehensive context, existing patterns to follow, and detailed validation loops. The main risk is API authentication setup, which is well-documented with fallback strategies.