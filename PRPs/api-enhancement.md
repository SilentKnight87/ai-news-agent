name: "API Enhancement - Search, Filtering, and Pagination PRP"
description: |

## Purpose
Implement comprehensive API enhancements including full-text search, advanced filtering, pagination, digest management, and analytics endpoints for the AI News Aggregator frontend consumption.

## Core Principles
1. **Pattern Consistency**: Follow existing FastAPI patterns in `src/api/routes.py`
2. **Performance First**: Implement caching, indexing, and query optimization
3. **MCP Integration**: Use Supabase MCP for database operations and validation
4. **Response Standardization**: Consistent pagination and error formats
5. **Progressive Enhancement**: Start with MVP endpoints, validate, then optimize

---

## Goal
Implement all missing API endpoints required for frontend consumption, focusing on search, filtering, pagination, and digest management as specified in `spec/api-enhancement.md`.

## Why
- **Frontend Blocked**: Netflix-style UI cannot be built without these endpoints
- **User Experience**: Enable fast content discovery through search and filters
- **Performance**: Current basic endpoints lack optimization for production scale
- **Analytics**: No visibility into content trends and source performance

## What
Enhanced REST API with:
- Full-text search across article titles and content
- Advanced filtering by date ranges, sources, and relevance scores
- Standardized pagination with metadata
- Complete digest CRUD operations
- Source analytics and trending algorithms

### Success Criteria
- [ ] All MVP endpoints implemented and returning data
- [ ] Search queries complete in < 200ms
- [ ] Pagination metadata consistent across all endpoints
- [ ] Database indexes created and utilized
- [ ] Response caching implemented
- [ ] All endpoints documented in OpenAPI
- [ ] Integration tests passing

## All Needed Context

### Documentation & References
```yaml
# MUST READ - Include these in your context window
- url: https://fastapi.tiangolo.com/tutorial/query-params/
  why: Query parameter validation patterns
  
- url: https://fastapi.tiangolo.com/advanced/middleware/
  why: Response caching middleware implementation
  
- file: src/api/routes.py
  why: Existing route patterns, dependency injection, error handling
  
- file: src/repositories/articles.py
  why: Database query patterns, existing methods to extend
  
- file: src/models/schemas.py
  why: Response model patterns, pagination structure
  
- doc: https://supabase.com/docs/guides/database/full-text-search
  section: PostgreSQL full-text search setup
  critical: GIN index creation for performance

- docfile: spec/api-enhancement.md
  why: Complete specification with endpoint details

# MCP Tool Documentation
- mcp: mcp__supabase__apply_migration
  why: Create database indexes for search performance
  
- mcp: mcp__supabase__execute_sql
  why: Test queries and verify index usage
  
- mcp: mcp__supabase__get_advisors
  why: Validate performance optimizations
  
- mcp: mcp__context7__get-library-docs
  params: /tiangolo/fastapi, topic="pagination,caching,middleware"
  why: Latest FastAPI patterns and best practices
```

### Current Codebase Structure
```bash
src/
├── api/
│   ├── routes.py          # Existing endpoints to extend
│   └── dependencies.py    # Dependency injection patterns
├── models/
│   ├── articles.py        # Article model
│   └── schemas.py         # Pydantic schemas
├── repositories/
│   └── articles.py        # ArticleRepository to extend
├── services/
│   ├── deduplication.py
│   └── scheduler.py
└── main.py               # FastAPI app with middleware
```

### Desired Codebase Structure
```bash
src/
├── api/
│   ├── routes.py          # Extended with new endpoints
│   ├── search.py          # New: Search-specific routes
│   ├── analytics.py       # New: Analytics endpoints
│   └── dependencies.py    # Extended with cache dependency
├── models/
│   └── schemas.py         # Extended with new response models
├── repositories/
│   └── articles.py        # Extended with search methods
├── services/
│   └── cache.py          # New: Redis-based caching service
└── utils/
    └── pagination.py      # New: Pagination utilities
```

### Known Gotchas & Critical Context
```python
# CRITICAL: Supabase enum limitation
# The articles.source column only supports: arxiv, hackernews, rss
# New sources (youtube, reddit, github, huggingface) are mapped to 'rss'
# Actual source preserved in metadata["_actual_source"]

# CRITICAL: Vector embedding format
# Embeddings are stored as JSON strings, must parse before use
# embedding = json.loads(data["embedding"]) 

# CRITICAL: RLS policies affect performance
# Current RLS policies cause re-evaluation per row
# Fix: Replace auth.uid() with (select auth.uid())

# CRITICAL: Missing indexes from Supabase advisor
# articles.duplicate_of needs index
# digest_articles.article_id needs index

# PATTERN: Dependency injection
# Always use Annotated[Type, Depends(factory)] pattern
# Example: article_repo: Annotated[ArticleRepository, Depends(get_article_repository)]

# PATTERN: Async everywhere
# All route handlers and repository methods must be async
# Use asyncio for concurrent operations
```

## Implementation Blueprint

### Data Models and Schemas
```python
# src/models/schemas.py - Add these response models

class PaginationMetadata(BaseModel):
    """Standardized pagination metadata."""
    page: int
    per_page: int
    total: int
    total_pages: int
    has_next: bool
    has_prev: bool

class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response wrapper."""
    data: list[T]
    pagination: PaginationMetadata
    meta: dict = Field(default_factory=lambda: {"cache_hit": False})

class SearchRequest(BaseModel):
    """Search query parameters."""
    q: str = Field(..., min_length=2, description="Search query")
    source: ArticleSource | None = None
    limit: int = Field(20, ge=1, le=100)
    offset: int = Field(0, ge=0)

class FilterRequest(BaseModel):
    """Advanced filter parameters."""
    start_date: datetime | None = None
    end_date: datetime | None = None
    relevance_min: float = Field(None, ge=0, le=100)
    source: ArticleSource | None = None
    categories: list[str] | None = None

class SourceStats(BaseModel):
    """Source statistics response."""
    source: ArticleSource
    article_count: int
    last_fetch: datetime | None
    avg_relevance_score: float
    categories: list[str]

class DigestCreateRequest(BaseModel):
    """Manual digest generation request."""
    limit: int = Field(10, ge=1, le=50)
    theme: str | None = None
    since_hours: int = Field(24, ge=1, le=168)
```

### Task List

```yaml
Task 1: Database Index Creation
EXECUTE via MCP:
  - mcp__supabase__apply_migration:
      name: "add_search_and_performance_indexes"
      query: |
        -- Full-text search index
        CREATE INDEX IF NOT EXISTS idx_articles_content_search 
        ON articles USING gin(to_tsvector('english', title || ' ' || content));
        
        -- Performance indexes
        CREATE INDEX IF NOT EXISTS idx_articles_source_date 
        ON articles(source, published_at DESC);
        
        CREATE INDEX IF NOT EXISTS idx_articles_relevance 
        ON articles(relevance_score DESC) WHERE relevance_score IS NOT NULL;
        
        -- Fix missing indexes from advisor
        CREATE INDEX IF NOT EXISTS idx_articles_duplicate_of 
        ON articles(duplicate_of);
        
        CREATE INDEX IF NOT EXISTS idx_digest_articles_article_id 
        ON digest_articles(article_id);
        
        -- Digest performance
        CREATE INDEX IF NOT EXISTS idx_digests_created 
        ON daily_digests(created_at DESC);

Task 2: Create Pagination Utilities
CREATE src/utils/pagination.py:
  - PATTERN: Reusable pagination logic
  - CALCULATE: total pages, has_next, has_prev
  - VALIDATE: page boundaries

Task 3: Extend Repository with Search Methods
MODIFY src/repositories/articles.py:
  - ADD method: search_articles() with full-text search
  - ADD method: filter_articles() with date/relevance filters
  - ADD method: get_trending_articles() with algorithm
  - ADD method: get_source_stats() for analytics
  - PATTERN: Use existing _db_dict_to_article conversion

Task 4: Create Cache Service
CREATE src/services/cache.py:
  - PATTERN: Similar to deduplication service structure
  - USE: In-memory cache with TTL (Redis later)
  - METHODS: get(), set(), invalidate()
  - DECORATOR: @cache_result(ttl=300)

Task 5: Implement Search Endpoints
MODIFY src/api/routes.py:
  - ADD: GET /api/articles/search
  - ADD: GET /api/articles/filter
  - ADD: GET /api/articles/trending
  - PATTERN: Follow existing error handling
  - USE: PaginatedResponse wrapper

Task 6: Enhance Article Listing
MODIFY src/api/routes.py - list_articles():
  - ADD: page/per_page parameters
  - ADD: sort_by and order parameters
  - RETURN: PaginatedResponse instead of ArticleListResponse
  - PRESERVE: Existing filtering logic

Task 7: Implement Digest CRUD
MODIFY src/api/routes.py:
  - ADD: GET /api/digests with pagination
  - ADD: GET /api/digests/{id}
  - ADD: POST /api/digests/generate
  - ADD: DELETE /api/digests/{id}
  - PATTERN: Use existing digest generation logic

Task 8: Create Analytics Endpoints
CREATE src/api/analytics.py:
  - ADD: GET /api/sources - source statistics
  - ADD: GET /api/analytics/trending-topics
  - ADD: GET /api/analytics/fetch-stats
  - INCLUDE: In main router

Task 9: Add Response Caching
MODIFY src/main.py:
  - ADD: Custom caching middleware
  - PATTERN: Use @app.middleware("http")
  - CACHE: GET requests with cache headers
  - SKIP: POST/PUT/DELETE requests
```

### Per-Task Implementation Details

```python
# Task 2: Pagination Utilities
# src/utils/pagination.py
async def paginate_query(
    query: Any,  # Supabase query builder
    page: int = 1,
    per_page: int = 20
) -> tuple[list, PaginationMetadata]:
    # Calculate offset
    offset = (page - 1) * per_page
    
    # Get total count
    count_result = await query.count()
    total = count_result.count
    
    # Get paginated results
    results = await query.range(offset, offset + per_page - 1).execute()
    
    # Calculate metadata
    total_pages = (total + per_page - 1) // per_page
    
    return results.data, PaginationMetadata(
        page=page,
        per_page=per_page,
        total=total,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1
    )

# Task 3: Repository Search Method
# Add to ArticleRepository
async def search_articles(
    self,
    query: str,
    source: ArticleSource | None = None,
    limit: int = 20,
    offset: int = 0
) -> list[Article]:
    try:
        # Build base query with full-text search
        search_query = self.supabase.rpc(
            "search_articles",  # Create this function
            {
                "search_query": query,
                "result_limit": limit,
                "result_offset": offset
            }
        )
        
        # Add source filter if provided
        if source:
            search_query = search_query.eq("source", source.value)
            
        response = await search_query.execute()
        
        # Convert results
        return [self._db_dict_to_article(item) for item in response.data]
        
    except Exception as e:
        logger.error(f"Search failed: {e}")
        return []

# Task 5: Search Endpoint
# Add to routes.py
@router.get("/api/articles/search", response_model=PaginatedResponse[Article])
async def search_articles(
    q: str = Query(..., min_length=2),
    source: ArticleSource | None = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    article_repo: Annotated[ArticleRepository, Depends(get_article_repository)],
    cache_service: Annotated[CacheService, Depends(get_cache_service)]
) -> PaginatedResponse[Article]:
    # Check cache
    cache_key = f"search:{q}:{source}:{page}:{per_page}"
    cached = await cache_service.get(cache_key)
    if cached:
        return cached
    
    # Perform search
    articles = await article_repo.search_articles(
        query=q,
        source=source,
        limit=per_page,
        offset=(page - 1) * per_page
    )
    
    # Get total count for pagination
    total = await article_repo.count_search_results(q, source)
    
    # Build response
    response = PaginatedResponse(
        data=articles,
        pagination=PaginationMetadata(
            page=page,
            per_page=per_page,
            total=total,
            total_pages=(total + per_page - 1) // per_page,
            has_next=page * per_page < total,
            has_prev=page > 1
        ),
        meta={"cache_hit": False, "query": q}
    )
    
    # Cache for 5 minutes
    await cache_service.set(cache_key, response, ttl=300)
    
    return response

# Task 9: Caching Middleware
# Add to main.py
@app.middleware("http")
async def cache_middleware(request: Request, call_next):
    # Only cache GET requests
    if request.method != "GET":
        return await call_next(request)
    
    # Skip cache for certain paths
    if any(path in str(request.url) for path in ["/docs", "/health", "/admin"]):
        return await call_next(request)
    
    # Generate cache key
    cache_key = f"{request.url.path}:{request.url.query}"
    
    # Check cache
    cached = cache.get(cache_key)
    if cached:
        return JSONResponse(
            content=cached,
            headers={"X-Cache": "HIT"}
        )
    
    # Process request
    response = await call_next(request)
    
    # Cache successful responses
    if response.status_code == 200:
        # Read response body
        body = b""
        async for chunk in response.body_iterator:
            body += chunk
        
        # Cache for 5 minutes
        cache.set(cache_key, json.loads(body), ttl=300)
        
        # Return new response with cache header
        return Response(
            content=body,
            status_code=response.status_code,
            headers={**response.headers, "X-Cache": "MISS"},
            media_type=response.media_type
        )
    
    return response
```

### Integration Points
```yaml
DATABASE:
  - migration: "Create search indexes and functions"
  - function: |
      CREATE OR REPLACE FUNCTION search_articles(
        search_query TEXT,
        result_limit INT DEFAULT 20,
        result_offset INT DEFAULT 0
      )
      RETURNS TABLE(LIKE articles) AS $$
      BEGIN
        RETURN QUERY
        SELECT a.*
        FROM articles a
        WHERE to_tsvector('english', a.title || ' ' || a.content) 
              @@ plainto_tsquery('english', search_query)
        ORDER BY ts_rank(
          to_tsvector('english', a.title || ' ' || a.content),
          plainto_tsquery('english', search_query)
        ) DESC
        LIMIT result_limit
        OFFSET result_offset;
      END;
      $$ LANGUAGE plpgsql;
  
CONFIG:
  - add to: src/config.py
  - pattern: |
      CACHE_TTL = int(os.getenv('CACHE_TTL', '300'))
      SEARCH_MIN_LENGTH = int(os.getenv('SEARCH_MIN_LENGTH', '2'))
  
ROUTES:
  - modify: src/main.py
  - pattern: |
      from .api import analytics
      app.include_router(analytics.router, prefix="/api/v1")
```

## Validation Loop

### Level 1: Syntax & Style
```bash
# Run these FIRST - fix any errors before proceeding
cd /Users/peterbrown/Documents/Code/ai-news-aggregator-agent
source .venv/bin/activate  # or your venv path

ruff check src/api/ --fix
ruff check src/repositories/ --fix
ruff check src/utils/ --fix
mypy src/api/routes.py
mypy src/repositories/articles.py

# Expected: No errors. If errors, READ and fix.
```

### Level 2: Database Validation
```bash
# Verify indexes created
mcp__supabase__execute_sql(
  query="SELECT indexname FROM pg_indexes WHERE tablename = 'articles';"
)

# Test search function
mcp__supabase__execute_sql(
  query="SELECT * FROM search_articles('machine learning', 10, 0) LIMIT 1;"
)

# Check performance advisor
mcp__supabase__get_advisors(type="performance")
# Expected: No warnings about missing indexes
```

### Level 3: Unit Tests
```python
# CREATE tests/test_api/test_search.py
import pytest
from httpx import AsyncClient
from src.main import app

@pytest.mark.asyncio
async def test_search_endpoint():
    """Test search returns paginated results."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/api/articles/search?q=AI")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "pagination" in data
        assert data["pagination"]["page"] == 1

@pytest.mark.asyncio
async def test_search_validation():
    """Test search query validation."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/api/articles/search?q=a")
        assert response.status_code == 422  # Query too short

@pytest.mark.asyncio
async def test_filter_endpoint():
    """Test filtering with date range."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/api/articles/filter"
            "?start_date=2024-01-01T00:00:00"
            "&relevance_min=70"
        )
        assert response.status_code == 200
        data = response.json()
        assert all(a["relevance_score"] >= 70 for a in data["data"])

@pytest.mark.asyncio
async def test_cache_headers():
    """Test caching middleware adds headers."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # First request - cache miss
        response1 = await client.get("/api/v1/api/sources")
        assert response1.headers.get("X-Cache") == "MISS"
        
        # Second request - cache hit
        response2 = await client.get("/api/v1/api/sources")
        assert response2.headers.get("X-Cache") == "HIT"
```

```bash
# Run tests
uv run pytest tests/test_api/test_search.py -v

# If failing: Check logs, fix implementation, re-run
```

### Level 4: Integration Test
```bash
# Start the service
uv run python -m src.main

# Test search endpoint
curl -X GET "http://localhost:8000/api/v1/api/articles/search?q=machine%20learning&page=1&per_page=10" \
  -H "Accept: application/json"

# Expected response format:
{
  "data": [...],
  "pagination": {
    "page": 1,
    "per_page": 10,
    "total": 150,
    "total_pages": 15,
    "has_next": true,
    "has_prev": false
  },
  "meta": {
    "cache_hit": false,
    "query": "machine learning"
  }
}

# Test filter endpoint
curl -X GET "http://localhost:8000/api/v1/api/articles/filter?start_date=2024-01-01&relevance_min=80&source=arxiv"

# Test digest generation
curl -X POST "http://localhost:8000/api/v1/api/digests/generate?limit=5&theme=LLMs" \
  -H "Content-Type: application/json"

# Performance test - should be < 200ms
time curl -X GET "http://localhost:8000/api/v1/api/articles/search?q=transformer"
```

## MCP Validation Commands
```yaml
# After implementation, run these MCP commands to validate:

# 1. Check all indexes created
mcp__supabase__execute_sql:
  query: |
    SELECT schemaname, tablename, indexname 
    FROM pg_indexes 
    WHERE tablename IN ('articles', 'daily_digests', 'digest_articles')
    ORDER BY tablename, indexname;

# 2. Test search performance
mcp__supabase__execute_sql:
  query: |
    EXPLAIN ANALYZE
    SELECT * FROM articles
    WHERE to_tsvector('english', title || ' ' || content) 
          @@ plainto_tsquery('english', 'artificial intelligence')
    LIMIT 20;

# 3. Verify no performance issues remain
mcp__supabase__get_advisors:
  type: "performance"

# Expected: Execution time < 50ms for search queries
# Expected: No critical performance advisories
```

## Final Validation Checklist
- [ ] All 9 tasks completed successfully
- [ ] Database indexes created and being used
- [ ] Search queries return results in < 200ms
- [ ] Pagination metadata consistent across all endpoints
- [ ] Response caching working (check X-Cache headers)
- [ ] All MVP endpoints responding with correct data
- [ ] Error responses follow standard format
- [ ] No type errors: `uv run mypy src/`
- [ ] All tests pass: `uv run pytest tests/test_api/ -v`
- [ ] Manual integration tests successful
- [ ] OpenAPI docs show all new endpoints

---

## Anti-Patterns to Avoid
- ❌ Don't use LIKE queries for search - use full-text search
- ❌ Don't load all articles then filter in Python - filter in DB
- ❌ Don't create new response formats - use PaginatedResponse
- ❌ Don't skip cache invalidation on writes
- ❌ Don't ignore the source enum mapping issue
- ❌ Don't use synchronous database calls in async handlers
- ❌ Don't catch broad exceptions - be specific
- ❌ Don't hardcode pagination limits - use config

## Performance Optimization Notes
1. **Search Index**: GIN index on tsvector is critical for sub-200ms search
2. **Pagination**: Always use LIMIT/OFFSET in database, never in Python
3. **Caching**: Cache search results but invalidate on new articles
4. **Connection Pooling**: Supabase client already handles this
5. **Concurrent Queries**: Use asyncio.gather() for multiple queries

## Score: 9/10
High confidence in one-pass implementation due to:
- Comprehensive context from existing codebase
- Clear patterns to follow from current implementation  
- MCP tools for database operations and validation
- Detailed validation gates at each level
- Specific performance requirements and testing

The 1-point deduction is for potential edge cases in search relevance ranking that may require tuning based on real data.