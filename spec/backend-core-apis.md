# Backend Core APIs Specification

## FEATURE:

- Core REST API endpoints required for MVP frontend functionality
- Full-text search capability across article titles and content
- Advanced filtering by date ranges, sources, and relevance scores
- Standardized pagination with consistent metadata across all list endpoints
- Complete digest management endpoints for audio and text content
- Source metadata endpoint for dynamic UI population
- Optimized database queries with proper indexing for sub-200ms response times
- Consistent error handling and response formats
- Integration with existing backend services (repositories, analyzers, fetchers)
- Frontend-ready response structures matching TypeScript interfaces

## MVP CORE APIS (Required for v1):

### 1. **Article Search API**
`GET /api/v1/articles/search`

**Purpose**: Enable users to search across all article content
**Frontend Usage**: Search bar in header, search results page

**Query Parameters**:
- `q` (string, required): Search query text
- `source` (string, optional): Filter by specific source
- `limit` (int, optional, default=20): Number of results
- `offset` (int, optional, default=0): Pagination offset

**Response Structure**:
```json
{
  "articles": [
    {
      "id": "uuid",
      "title": "string",
      "summary": "string",
      "source": "arxiv|hackernews|rss|youtube|reddit|github|huggingface",
      "url": "string",
      "published_at": "2025-01-10T12:00:00Z",
      "relevance_score": 85,
      "categories": ["research", "llm"],
      "thumbnail_url": "string|null"
    }
  ],
  "total": 145,
  "query": "transformer architecture",
  "took_ms": 45
}
```

**Implementation Notes**:
- Use PostgreSQL full-text search with GIN index
- Search in title and content fields
- Order by relevance score combined with text search rank
- Cache frequent queries for 5 minutes

### 2. **Article Filter API**
`GET /api/v1/articles/filter`

**Purpose**: Advanced filtering for content discovery
**Frontend Usage**: Filter bar below hero section

**Query Parameters**:
- `start_date` (date, optional): Filter articles after this date
- `end_date` (date, optional): Filter articles before this date
- `relevance_min` (int, optional): Minimum relevance score (0-100)
- `relevance_max` (int, optional): Maximum relevance score (0-100)
- `sources` (string, optional): Comma-separated source list
- `categories` (string, optional): Comma-separated category list
- `limit` (int, optional, default=20): Results per page
- `offset` (int, optional, default=0): Pagination offset

**Response Structure**:
```json
{
  "articles": [...],  // Same article structure as search
  "filters_applied": {
    "start_date": "2025-01-01",
    "end_date": "2025-01-10",
    "relevance_min": 70,
    "sources": ["arxiv", "hackernews"]
  },
  "total": 89,
  "took_ms": 32
}
```

**Implementation Notes**:
- Build dynamic WHERE clause based on provided filters
- Use composite indexes for common filter combinations
- Default to last 7 days if no date range specified

### 3. **Enhanced Articles List with Pagination**
`GET /api/v1/articles`

**Purpose**: Replace current basic endpoint with proper pagination
**Frontend Usage**: Main content rows, category pages

**Query Parameters**:
- `page` (int, optional, default=1): Page number (1-indexed)
- `per_page` (int, optional, default=20, max=100): Items per page
- `sort_by` (string, optional): Field to sort by (published_at|relevance_score|title)
- `order` (string, optional): Sort order (asc|desc, default=desc)
- `source` (string, optional): Filter by source

**Response Structure**:
```json
{
  "articles": [...],  // Article array
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 211,
    "total_pages": 11,
    "has_next": true,
    "has_prev": false
  },
  "meta": {
    "sort_by": "published_at",
    "order": "desc",
    "cache_hit": false
  }
}
```

**Implementation Notes**:
- Calculate total_pages from total and per_page
- Use LIMIT and OFFSET for pagination
- Add index on sort fields

### 4. **Digest List API**
`GET /api/v1/digests`

**Purpose**: List all available digests with pagination
**Frontend Usage**: Digest archive page, audio playlist

**Query Parameters**:
- `page` (int, optional, default=1): Page number
- `per_page` (int, optional, default=10): Digests per page

**Response Structure**:
```json
{
  "digests": [
    {
      "id": "uuid",
      "date": "2025-01-10",
      "title": "AI Daily: Breaking developments in multimodal models",
      "summary": "string",
      "key_developments": ["point1", "point2", "point3"],
      "article_count": 15,
      "audio_url": "string|null",
      "audio_duration": 300,
      "created_at": "2025-01-10T17:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 10,
    "total": 45,
    "total_pages": 5,
    "has_next": true,
    "has_prev": false
  }
}
```

**Implementation Notes**:
- Join with digest_articles for article_count
- Order by date DESC by default
- Include audio metadata if available

### 5. **Single Digest API**
`GET /api/v1/digests/{digest_id}`

**Purpose**: Get complete digest with all articles
**Frontend Usage**: Digest detail page, audio player

**Response Structure**:
```json
{
  "id": "uuid",
  "date": "2025-01-10",
  "title": "AI Daily: Breaking developments in multimodal models",
  "summary": "Full digest summary text...",
  "key_developments": [
    "OpenAI releases new model",
    "Google announces breakthrough",
    "Meta open sources tool"
  ],
  "articles": [
    {
      "id": "uuid",
      "title": "string",
      "summary": "string",
      "source": "arxiv",
      "url": "string",
      "relevance_score": 92
    }
  ],
  "audio_url": "string|null",
  "audio_duration": 300,
  "created_at": "2025-01-10T17:00:00Z",
  "updated_at": "2025-01-10T17:05:00Z"
}
```

**Implementation Notes**:
- Single query with JOIN on digest_articles and articles
- Return 404 if digest not found
- Include full article details for digest display

### 6. **Sources Metadata API**
`GET /api/v1/sources`

**Purpose**: List all sources with statistics
**Frontend Usage**: Filter dropdown, source statistics page

**Response Structure**:
```json
{
  "sources": [
    {
      "name": "arxiv",
      "display_name": "ArXiv",
      "description": "Academic papers and preprints",
      "article_count": 84,
      "last_fetch": "2025-01-10T12:00:00Z",
      "status": "active",
      "icon_url": "/icons/arxiv.svg",
      "categories": ["research", "papers"]
    },
    {
      "name": "hackernews",
      "display_name": "Hacker News",
      "description": "Technology and startup news",
      "article_count": 0,
      "last_fetch": "2025-01-10T12:00:00Z",
      "status": "active",
      "icon_url": "/icons/hn.svg",
      "categories": ["news", "discussion"]
    }
  ],
  "total_sources": 7,
  "active_sources": 6,
  "total_articles": 211
}
```

**Implementation Notes**:
- Aggregate article counts by source
- Get last_fetch from fetcher status
- Include hardcoded metadata (descriptions, icons)
- Cache for 1 minute

## IMPLEMENTATION REQUIREMENTS:

### Database Indexes:
```sql
-- Full-text search index
CREATE INDEX idx_articles_fulltext ON articles 
USING gin(to_tsvector('english', title || ' ' || content));

-- Filter performance
CREATE INDEX idx_articles_date_relevance ON articles(published_at DESC, relevance_score DESC);
CREATE INDEX idx_articles_source_date ON articles(source, published_at DESC);

-- Digest queries
CREATE INDEX idx_digests_date ON daily_digests(date DESC);
CREATE INDEX idx_digest_articles_composite ON digest_articles(digest_id, article_id);
```

### FastAPI Implementation Pattern:
```python
from fastapi import Query
from typing import Optional, List
from datetime import date

@router.get("/api/v1/articles/search")
async def search_articles(
    q: str = Query(..., description="Search query"),
    source: Optional[str] = Query(None, description="Filter by source"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    article_repo: ArticleRepository = Depends(get_article_repository)
):
    """Search articles with full-text search."""
    # Implementation here
    pass
```

### Error Response Format:
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid date format",
    "field": "start_date",
    "timestamp": "2025-01-10T12:00:00Z"
  }
}
```

### Performance Requirements:
- All list endpoints must respond in < 200ms (p95)
- Search queries must complete in < 300ms (p95)
- Use connection pooling with min=5, max=20 connections
- Implement query result caching with 5-minute TTL
- Add request ID logging for debugging

### Testing Requirements:
- Unit tests for each endpoint with mock repositories
- Integration tests with test database
- Load testing with 100 concurrent requests
- Test pagination edge cases (empty results, last page)
- Test invalid parameter combinations

## EXAMPLES:

### Search for LLM papers:
```bash
GET /api/v1/articles/search?q=large+language+models&source=arxiv&limit=10

# Returns top 10 ArXiv papers about LLMs
```

### Filter recent high-relevance articles:
```bash
GET /api/v1/articles/filter?start_date=2025-01-05&relevance_min=80&sources=arxiv,hackernews

# Returns articles from last 5 days with relevance >= 80
```

### Get page 2 of articles:
```bash
GET /api/v1/articles?page=2&per_page=20&sort_by=relevance_score&order=desc

# Returns articles 21-40 sorted by relevance
```

### Get latest digest with audio:
```bash
GET /api/v1/digests?page=1&per_page=1

# Returns most recent digest with audio_url if available
```

## FRONTEND INTEGRATION:

### TypeScript Interfaces:
```typescript
interface Article {
  id: string;
  title: string;
  summary: string;
  source: ArticleSource;
  url: string;
  published_at: string;
  relevance_score: number;
  categories: string[];
  thumbnail_url?: string;
}

interface PaginationMeta {
  page: number;
  per_page: number;
  total: number;
  total_pages: number;
  has_next: boolean;
  has_prev: boolean;
}

interface ArticleListResponse {
  articles: Article[];
  pagination: PaginationMeta;
}
```

### Frontend Usage Examples:
```typescript
// Search articles
const results = await fetch('/api/v1/articles/search?q=transformers');

// Filter with date range
const filtered = await fetch('/api/v1/articles/filter?start_date=2025-01-01&relevance_min=70');

// Get paginated articles
const page2 = await fetch('/api/v1/articles?page=2&per_page=20');

// Load digest for audio player
const digest = await fetch('/api/v1/digests/123-456');
```

## MIGRATION PATH:

1. **Phase 1**: Implement new endpoints alongside existing ones
2. **Phase 2**: Update frontend to use new endpoints
3. **Phase 3**: Deprecate old endpoints after frontend migration
4. **Phase 4**: Remove deprecated endpoints in next release

## SUCCESS METRICS:

- [ ] All 6 core APIs implemented and tested
- [ ] Average response time < 200ms
- [ ] Frontend successfully consuming all endpoints
- [ ] Search functionality working with < 300ms response
- [ ] Pagination working correctly across all list endpoints
- [ ] Proper error handling with consistent format
- [ ] API documentation updated in OpenAPI/Swagger