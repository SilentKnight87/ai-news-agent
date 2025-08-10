name: "Backend Core APIs - Search, Filter, Pagination, and Digests PRP"
description: |

## Purpose
Implement 6 core MVP REST API endpoints for search, filtering, pagination, digest management, and source metadata as specified in `spec/backend-core-apis.md`. These APIs are critical for frontend functionality and must follow existing patterns in the codebase.

## Core Principles
1. **Pattern Consistency**: Follow existing FastAPI patterns in `src/api/routes.py`
2. **Repository Pattern**: Extend `ArticleRepository` with new query methods
3. **Performance First**: Use database indexes and implement caching
4. **Error Handling**: Use existing HTTPException patterns with proper status codes
5. **MCP Integration**: Use Supabase MCP for database operations and schema validation

---

## Goal
Implement all 6 missing MVP API endpoints that are blocking frontend development:
1. Article search with full-text capability
2. Advanced filtering by date/relevance/source
3. Enhanced pagination with proper metadata
4. Digest list with pagination
5. Single digest retrieval
6. Sources metadata endpoint

## Why
- **Frontend Blocked**: Netflix-style UI cannot function without these endpoints
- **User Experience**: No search or filter capability currently exists
- **Performance**: Current `/articles` endpoint lacks proper pagination
- **Audio Integration**: No digest endpoints for audio player functionality

## What
6 new REST API endpoints with:
- PostgreSQL full-text search using GIN indexes
- Dynamic filtering with composite indexes
- Standardized pagination response format
- Digest management with audio metadata
- Source statistics aggregation
- Sub-200ms response times (p95)

### Success Criteria
- [ ] All 6 endpoints implemented and returning correct data
- [ ] Full-text search completes in < 300ms
- [ ] Filter queries complete in < 200ms
- [ ] Pagination metadata consistent across all endpoints
- [ ] Database indexes created and utilized
- [ ] All unit tests passing
- [ ] Integration tests with test database passing
- [ ] Frontend successfully consuming endpoints

## All Needed Context

### Documentation & References
```yaml
# MUST READ - FastAPI documentation
- url: https://fastapi.tiangolo.com/tutorial/query-params/
  why: Query parameter validation patterns for search/filter
  
- url: https://fastapi.tiangolo.com/tutorial/dependencies/
  why: Dependency injection patterns we're using

- url: https://www.postgresql.org/docs/current/textsearch.html
  why: Full-text search implementation details
```

### MCP Tool Usage

#### Pre-Implementation Research:
```bash
# 1. Get latest FastAPI documentation for query params and dependencies
mcp__context7__resolve-library-id("fastapi")
mcp__context7__get-library-docs("/tiangolo/fastapi", topic="query parameters dependencies")

# 2. Check current database schema and indexes
mcp__supabase__list_tables(schemas=["public"])
mcp__supabase__execute_sql("SELECT indexname, indexdef FROM pg_indexes WHERE tablename = 'articles';")
mcp__supabase__execute_sql("SELECT indexname, indexdef FROM pg_indexes WHERE tablename = 'daily_digests';")
```

#### Implementation Database Operations:
```bash
# 3. Create required indexes for search and filtering
mcp__supabase__apply_migration(
  name="add_fulltext_search_indexes",
  query="""
    -- Full-text search index
    CREATE INDEX IF NOT EXISTS idx_articles_fulltext 
    ON articles USING gin(to_tsvector('english', title || ' ' || content));
    
    -- Composite index for date and relevance filtering
    CREATE INDEX IF NOT EXISTS idx_articles_date_relevance 
    ON articles(published_at DESC, relevance_score DESC);
    
    -- Source and date composite for source filtering
    CREATE INDEX IF NOT EXISTS idx_articles_source_date 
    ON articles(source, published_at DESC);
    
    -- Categories GIN index for category filtering
    CREATE INDEX IF NOT EXISTS idx_articles_categories 
    ON articles USING gin(categories);
    
    -- Digest date index
    CREATE INDEX IF NOT EXISTS idx_digests_date 
    ON daily_digests(digest_date DESC);
    
    -- Composite index for digest_articles
    CREATE INDEX IF NOT EXISTS idx_digest_articles_composite 
    ON digest_articles(digest_id, article_id);
  """
)
```

### Existing Code Patterns to Follow

#### 1. Current API Route Pattern (`src/api/routes.py`):
```python
@router.get("/articles", response_model=ArticleListResponse)
async def list_articles(
    limit: int = 20,
    offset: int = 0,
    source: ArticleSource | None = None,
    min_relevance_score: int | None = None,
    since_hours: int | None = None,
    article_repo: Annotated[ArticleRepository, Depends(get_article_repository)]
) -> ArticleListResponse:
    # Validation
    if limit > 100:
        limit = 100
    # Business logic
    articles = await article_repo.get_articles(...)
    # Response formatting
    return ArticleListResponse(...)
```

#### 2. Repository Pattern (`src/repositories/articles.py`):
```python
class ArticleRepository:
    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client
        
    async def get_articles(self, limit: int = 20, offset: int = 0, ...):
        query = self.supabase.table("articles").select("*")
        # Build query dynamically
        result = query.execute()
        return [Article(**item) for item in result.data]
```

#### 3. Error Handling Pattern:
```python
try:
    # Operation
except HTTPException:
    raise
except Exception as e:
    logger.error(f"Failed to {operation}: {e}")
    raise HTTPException(status_code=500, detail="Error message")
```

#### 4. Dependency Injection (`src/api/dependencies.py`):
```python
def get_article_repository(
    supabase: Annotated[Client, Depends(get_supabase_client)]
) -> ArticleRepository:
    return ArticleRepository(supabase)
```

### Database Schema Reference
```sql
-- Articles table (existing)
CREATE TABLE articles (
    id UUID PRIMARY KEY,
    source_id TEXT NOT NULL,
    source article_source NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    url TEXT NOT NULL,
    published_at TIMESTAMP WITH TIME ZONE NOT NULL,
    summary TEXT,
    relevance_score REAL,
    categories TEXT[],
    embedding vector(384)
);

-- Daily digests table (existing)  
CREATE TABLE daily_digests (
    id UUID PRIMARY KEY,
    digest_date DATE NOT NULL UNIQUE,
    summary_text TEXT NOT NULL,
    total_articles_processed INTEGER NOT NULL,
    audio_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL
);

-- Junction table (existing)
CREATE TABLE digest_articles (
    digest_id UUID REFERENCES daily_digests(id),
    article_id UUID REFERENCES articles(id),
    PRIMARY KEY (digest_id, article_id)
);
```

### Response Format Standards
All list endpoints must follow this pagination format:
```python
{
    "data": [...],  # Or specific field name like "articles", "digests"
    "pagination": {
        "page": 1,
        "per_page": 20,
        "total": 211,
        "total_pages": 11,
        "has_next": true,
        "has_prev": false
    }
}
```

## Files to Create/Modify

### 1. **Extend Repository** - `src/repositories/articles.py`
Add these methods to ArticleRepository:
- `search_articles(query: str, source: str = None, limit: int = 20, offset: int = 0)`
- `filter_articles(start_date: date = None, end_date: date = None, ...)`
- `get_articles_paginated(page: int, per_page: int, sort_by: str, order: str)`
- `get_total_count(filters: dict = None)`
- `get_sources_metadata()`
- `get_digests(page: int = 1, per_page: int = 10)`
- `get_digest_by_id(digest_id: UUID)`

### 2. **Add New Routes** - `src/api/routes.py`
Add 6 new route handlers following existing patterns

### 3. **Update Schemas** - `src/models/schemas.py`
Add response models:
- `SearchResponse`
- `FilterResponse`
- `PaginatedArticleResponse`
- `DigestListResponse`
- `DigestDetailResponse`
- `SourcesMetadataResponse`
- `PaginationMeta`

### 4. **Create Tests** - `tests/test_api/test_core_endpoints.py`
Full test coverage for all endpoints

## Implementation Blueprint

### Phase 1: Database Preparation
```python
# 1. Run migration via Supabase MCP (see MCP commands above)
# 2. Verify indexes created:
mcp__supabase__execute_sql("SELECT indexname FROM pg_indexes WHERE tablename IN ('articles', 'daily_digests');")
```

### Phase 2: Repository Extensions
```python
# src/repositories/articles.py

async def search_articles(
    self,
    query: str,
    source: ArticleSource | None = None,
    limit: int = 20,
    offset: int = 0
) -> tuple[list[Article], int]:
    """
    Full-text search across article titles and content.
    Returns (articles, total_count).
    """
    try:
        # Build search query using PostgreSQL full-text search
        search_query = f"""
            SELECT *, 
                   ts_rank(to_tsvector('english', title || ' ' || content), 
                          plainto_tsquery('english', $1)) as rank,
                   COUNT(*) OVER() as total_count
            FROM articles
            WHERE to_tsvector('english', title || ' ' || content) @@ 
                  plainto_tsquery('english', $1)
                  {f"AND source = '{source.value}'" if source else ""}
            ORDER BY rank DESC, published_at DESC
            LIMIT {limit} OFFSET {offset}
        """
        
        result = self.supabase.rpc(
            'search_articles',
            {'query_text': query, 'source_filter': source}
        ).execute()
        
        articles = [Article(**item) for item in result.data]
        total = result.data[0]['total_count'] if result.data else 0
        
        return articles, total
        
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise

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
    """
    query = self.supabase.table("articles").select("*, count:id.count()")
    
    # Apply filters dynamically
    if start_date:
        query = query.gte('published_at', start_date.isoformat())
    if end_date:
        query = query.lte('published_at', end_date.isoformat())
    if relevance_min is not None:
        query = query.gte('relevance_score', relevance_min)
    if relevance_max is not None:
        query = query.lte('relevance_score', relevance_max)
    if sources:
        query = query.in_('source', [s.value for s in sources])
    if categories:
        query = query.contains('categories', categories)
    
    # Order and paginate
    query = query.order('published_at', desc=True)
    query = query.range(offset, offset + limit - 1)
    
    result = query.execute()
    # ... rest of implementation
```

### Phase 3: API Routes Implementation
```python
# src/api/routes.py

from fastapi import Query
from typing import Optional
from datetime import date

@router.get("/api/v1/articles/search", response_model=SearchResponse)
async def search_articles(
    q: str = Query(..., description="Search query", min_length=1),
    source: Optional[ArticleSource] = Query(None, description="Filter by source"),
    limit: int = Query(20, ge=1, le=100, description="Results per page"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    article_repo: ArticleRepository = Depends(get_article_repository)
) -> SearchResponse:
    """
    Full-text search across article titles and content.
    
    Uses PostgreSQL full-text search with ranking.
    """
    try:
        start_time = time.time()
        
        articles, total = await article_repo.search_articles(
            query=q,
            source=source,
            limit=limit,
            offset=offset
        )
        
        took_ms = int((time.time() - start_time) * 1000)
        
        return SearchResponse(
            articles=articles,
            total=total,
            query=q,
            took_ms=took_ms
        )
        
    except Exception as e:
        logger.error(f"Search failed for query '{q}': {e}")
        raise HTTPException(
            status_code=500,
            detail="Search operation failed"
        )

# Similar pattern for other 5 endpoints...
```

### Phase 4: Response Models
```python
# src/models/schemas.py

class PaginationMeta(BaseModel):
    """Standard pagination metadata."""
    page: int
    per_page: int
    total: int
    total_pages: int
    has_next: bool
    has_prev: bool

class SearchResponse(BaseModel):
    """Search endpoint response."""
    articles: list[Article]
    total: int
    query: str
    took_ms: int

class PaginatedArticleResponse(BaseModel):
    """Enhanced article list with pagination."""
    articles: list[Article]
    pagination: PaginationMeta
    meta: dict[str, Any]
```

### Phase 5: Testing
```python
# tests/test_api/test_core_endpoints.py

import pytest
from fastapi.testclient import TestClient

@pytest.fixture
def test_articles(test_db):
    """Create test articles with various attributes."""
    # Create test data
    pass

def test_search_articles(client: TestClient, test_articles):
    """Test full-text search endpoint."""
    response = client.get("/api/v1/articles/search?q=transformer")
    assert response.status_code == 200
    data = response.json()
    assert "articles" in data
    assert "total" in data
    assert data["query"] == "transformer"
    
def test_filter_articles_date_range(client: TestClient, test_articles):
    """Test filtering by date range."""
    response = client.get(
        "/api/v1/articles/filter"
        "?start_date=2025-01-01"
        "&end_date=2025-01-10"
    )
    assert response.status_code == 200
    # ... more assertions

# Test all 6 endpoints with various scenarios
```

## Validation Gates

### Pre-Implementation Checks
```bash
# 1. Verify database connection
mcp__supabase__get_logs(service="postgres")

# 2. Check existing schema
mcp__supabase__list_tables(schemas=["public"])
```

### Post-Implementation Validation
```bash
# 1. Syntax and type checking
cd /Users/peterbrown/Documents/Code/ai-news-aggregator-agent
source venv_linux/bin/activate
ruff check src/api/routes.py src/repositories/articles.py --fix
mypy src/api/routes.py src/repositories/articles.py

# 2. Run unit tests
pytest tests/test_api/test_core_endpoints.py -v

# 3. Integration test with real database
pytest tests/test_api/test_core_endpoints.py --integration -v

# 4. Performance validation via Supabase MCP
mcp__supabase__execute_sql("""
    EXPLAIN ANALYZE
    SELECT * FROM articles
    WHERE to_tsvector('english', title || ' ' || content) @@ 
          plainto_tsquery('english', 'transformer')
    LIMIT 20;
""")

# 5. Check response times
curl -w "@curl-format.txt" -o /dev/null -s "http://localhost:8000/api/v1/articles/search?q=ai"
# Should be < 300ms

# 6. Verify all endpoints accessible
curl http://localhost:8000/docs
# Check all 6 new endpoints appear in OpenAPI docs
```

### MCP Validation Commands
```bash
# Verify indexes were created
mcp__supabase__execute_sql("SELECT indexname FROM pg_indexes WHERE tablename = 'articles' AND indexname LIKE 'idx_articles_%';")

# Check query performance
mcp__supabase__get_advisors(type="performance")

# Verify no security issues
mcp__supabase__get_advisors(type="security")
```

## Error Handling & Rollback

### Database Rollback (if needed)
```bash
mcp__supabase__apply_migration(
  name="rollback_search_indexes",
  query="""
    DROP INDEX IF EXISTS idx_articles_fulltext;
    DROP INDEX IF EXISTS idx_articles_date_relevance;
    DROP INDEX IF EXISTS idx_articles_source_date;
    DROP INDEX IF EXISTS idx_articles_categories;
  """
)
```

### Common Error Scenarios
1. **Search query too short**: Return 400 with clear message
2. **Invalid date format**: Return 422 with field-specific error
3. **Database timeout**: Return 503 with retry-after header
4. **No results found**: Return 200 with empty array, not 404

## Performance Optimization Notes

1. **Caching Strategy**:
   - Cache search results for 5 minutes (common queries)
   - Cache source metadata for 1 minute
   - No caching for user-specific filters

2. **Query Optimization**:
   - Use LIMIT + 1 trick to determine has_next efficiently
   - Use COUNT(*) OVER() for total count in same query
   - Avoid N+1 queries by using proper joins

3. **Index Usage**:
   - Full-text search: GIN index on tsvector
   - Date filtering: B-tree on published_at DESC
   - Source filtering: B-tree on source
   - Composite indexes for common filter combinations

## Success Metrics
- [ ] All 6 endpoints returning data in < 200ms (p95)
- [ ] Search functionality working with partial matches
- [ ] Pagination consistent across all endpoints
- [ ] Frontend successfully consuming all endpoints
- [ ] No N+1 query problems
- [ ] Database CPU usage < 20% under normal load
- [ ] All tests passing (unit + integration)

## Additional Notes

### Frontend Integration
The frontend team expects these exact response formats. Any deviation requires coordination. The TypeScript interfaces in the spec must match exactly.

### Migration Path
1. Deploy new endpoints alongside existing
2. Frontend migrates to new endpoints
3. Deprecate old `/articles` endpoint after migration
4. Remove deprecated code in next release

### Monitoring
After deployment, monitor:
- Response times per endpoint
- Search query patterns for cache optimization
- Database slow query log
- Error rates per endpoint

---

**Confidence Score: 9/10**

This PRP provides comprehensive context for implementing the 6 core backend APIs. The existing codebase patterns are well-documented, database operations are handled via MCP tools, and validation gates ensure quality. The only uncertainty is around potential edge cases in full-text search implementation, but the PostgreSQL documentation and MCP validation should handle this.