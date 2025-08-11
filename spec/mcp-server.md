# MCP Server Specification & Implementation Plan

**Last Updated:** January 11, 2025

## FEATURE OVERVIEW

- Model Context Protocol (MCP) server that exposes AI News Aggregator data and tools to AI assistants
- Direct integration with Claude, Cursor, and other MCP-compatible clients
- Real-time access to curated AI/ML news content, summaries, and analytics
- Content retrieval tools for ArXiv papers, HackerNews stories, and RSS feeds
- AI-powered analysis tools for summarization, trend analysis, and insights extraction
- Export and reporting capabilities in multiple formats (JSON, CSV, PDF, Markdown)
- Configuration management for RSS feeds, preferences, and analytics
- **PUBLIC DEPLOYMENT**: Designed for sharing with community while maintaining security
- **REMOTE HTTP-BASED**: Not local stdio - enables public sharing and centralized security

## CRITICAL DECISION: Architecture Choice

### **The Key Decision Factor: Python Backend Hosting Status**

The architecture depends entirely on one critical question:
**Is your Python backend already hosted with a stable public URL?**

---

### **Option A: If Python Backend IS Already Hosted**
✅ **Go with Hybrid Architecture** if you have:
- Stable public URL (e.g., `https://api.yourdomain.com`)
- Reliable hosting (DigitalOcean, AWS, Heroku with paid dyno, etc.)
- No cold start issues
- Already managing/paying for this infrastructure

**Benefits:**
- Maximum code reuse from existing backend
- Single source of truth for business logic
- No code duplication
- Existing tests continue to work

**Architecture:**
```
┌─────────────────────┐     ┌──────────────────────┐     ┌─────────────────────┐
│   MCP Clients       │────▶│  TypeScript MCP      │────▶│   Python Backend    │
│ (Claude/Cursor/etc) │     │  (Cloudflare Workers)│     │   (FastAPI)         │
└─────────────────────┘     └──────────────────────┘     └─────────────────────┘
       MCP Protocol              Thin Proxy Layer           Existing Business Logic
```

---

### **Option B: If Python Backend is NOT Hosted**
❌ **Avoid Hybrid - Go Pure TypeScript** because:

**Free Tier Python Hosting Reality:**
- **Render Free Tier**: Spins down after 15 min → 30+ second cold starts
- **Railway Free**: Only $5 credit/month, expires quickly
- **Fly.io Free**: Requires credit card, limited hours
- **Vercel Functions**: 10 second timeout, not suitable for database queries

**Architecture:**
```
┌─────────────────────┐     ┌──────────────────────┐     ┌─────────────────────┐
│   MCP Clients       │────▶│  TypeScript MCP      │────▶│   Supabase          │
│ (Claude/Cursor/etc) │     │  (Cloudflare Workers)│     │   (PostgreSQL)      │
└─────────────────────┘     └──────────────────────┘     └─────────────────────┘
       MCP Protocol              All Logic Here              Direct Connection
```

### Performance Comparison

| Metric | Hybrid (No Python Host) | Hybrid (With Python Host) | Pure TypeScript |
|--------|------------------------|---------------------------|-----------------|
| Cold Start | 30+ seconds (Render) | None | None |
| Latency | High (2 hops) | Medium (2 hops) | Low (1 hop) |
| Monthly Cost | $0-25 | $X (existing) | $0 |
| Complexity | High | Medium | Low |
| Code Reuse | High | High | None |
| Maintenance | 2 services | 2 services | 1 service |

## IMPLEMENTATION PATHS

## Path 1: HYBRID ARCHITECTURE (If Python Backend Hosted)

### Phase 1: Python Backend API Layer

#### 1.1 Create MCP API Endpoints
**File**: `src/api/mcp_endpoints.py`
```python
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from uuid import UUID

from ..repositories.articles import ArticleRepository
from ..models.articles import ArticleSource
from ..config import get_settings
from .auth import verify_api_key

router = APIRouter(prefix="/api/mcp", dependencies=[Depends(verify_api_key)])

@router.get("/articles/search")
async def search_articles(
    query: str,
    source: Optional[str] = None,
    limit: int = Query(20, le=100),
    offset: int = Query(0, ge=0),
    repo: ArticleRepository = Depends(get_article_repository)
) -> Dict[str, Any]:
    """Search articles endpoint for MCP server."""
    source_enum = ArticleSource(source) if source else None
    articles, total = await repo.search_articles(query, source_enum, limit, offset)
    
    return {
        "articles": [article.dict() for article in articles],
        "total": total,
        "limit": limit,
        "offset": offset
    }

@router.get("/articles/latest")
async def get_latest_articles(
    hours: int = Query(24, le=168),
    source: Optional[str] = None,
    limit: int = Query(50, le=100),
    repo: ArticleRepository = Depends(get_article_repository)
) -> Dict[str, Any]:
    """Get latest articles from the past N hours."""
    since = datetime.utcnow() - timedelta(hours=hours)
    source_enum = ArticleSource(source) if source else None
    
    articles = await repo.get_articles(
        limit=limit,
        source=source_enum,
        since=since,
        include_duplicates=False
    )
    
    return {
        "articles": [article.dict() for article in articles],
        "count": len(articles),
        "since": since.isoformat()
    }

@router.get("/stats")
async def get_stats(
    repo: ArticleRepository = Depends(get_article_repository)
) -> Dict[str, Any]:
    """Get database statistics."""
    return await repo.get_article_stats()
```

#### 1.2 API Authentication
**File**: `src/api/auth.py`
```python
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from ..config import get_settings

security = HTTPBearer()

def verify_api_key(credentials: HTTPAuthorizationCredentials = Security(security)):
    """Verify API key for MCP endpoints."""
    settings = get_settings()
    api_key = credentials.credentials
    
    valid_keys = settings.MCP_API_KEYS.split(",") if hasattr(settings, 'MCP_API_KEYS') else []
    
    if not api_key or api_key not in valid_keys:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    return api_key
```

### Phase 2: TypeScript MCP Server (Proxy Layer)

#### 2.1 Backend Client
**File**: `mcp-server/src/backend/client.ts`
```typescript
interface BackendConfig {
  apiUrl: string;
  apiKey: string;
  timeout?: number;
}

export class PythonBackendClient {
  private config: BackendConfig;

  constructor(config: BackendConfig) {
    this.config = {
      timeout: 30000,
      ...config
    };
  }

  private async request(endpoint: string, params?: any): Promise<any> {
    const url = new URL(`${this.config.apiUrl}/api/mcp${endpoint}`);
    
    if (params && Object.keys(params).length > 0) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          url.searchParams.append(key, String(value));
        }
      });
    }

    const response = await fetch(url.toString(), {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${this.config.apiKey}`,
        'Content-Type': 'application/json',
      },
      signal: AbortSignal.timeout(this.config.timeout!),
    });

    if (!response.ok) {
      throw new Error(`Backend API error: ${response.status} ${response.statusText}`);
    }

    return response.json();
  }

  async searchArticles(query: string, source?: string, limit?: number, offset?: number) {
    return this.request('/articles/search', { query, source, limit, offset });
  }

  async getLatestArticles(hours?: number, source?: string, limit?: number) {
    return this.request('/articles/latest', { hours, source, limit });
  }

  async getStats() {
    return this.request('/stats');
  }
}
```

#### 2.2 MCP Tools Registration
**File**: `mcp-server/src/tools/content.ts`
```typescript
import { z } from 'zod';
import { PythonBackendClient } from '../backend/client';
import { KVCache } from '../cache/kv';

export function registerContentTools(
  server: any,
  backend: PythonBackendClient,
  cache: KVCache
) {
  // Search Articles Tool
  server.registerTool(
    'search_articles',
    {
      title: 'Search Articles',
      description: 'Search AI news articles by query',
      inputSchema: z.object({
        query: z.string().describe('Search query'),
        source: z.string().optional().describe('Filter by source'),
        limit: z.number().optional().default(20).describe('Number of results'),
        offset: z.number().optional().default(0).describe('Pagination offset')
      })
    },
    async ({ query, source, limit, offset }) => {
      const cacheKey = cache.generateKey('search_articles', { query, source, limit, offset });
      const cached = await cache.get(cacheKey);
      if (cached) return cached;

      const result = await backend.searchArticles(query, source, limit, offset);
      await cache.set(cacheKey, result, 300);
      
      return result;
    }
  );
}
```

---

## Path 2: PURE TYPESCRIPT ARCHITECTURE (If No Python Backend)

### Implementation Structure
```
mcp-server/
├── src/
│   ├── index.ts           # Main Cloudflare Worker
│   ├── db/
│   │   └── queries.ts     # All database queries (ported from Python)
│   ├── tools/
│   │   └── index.ts       # MCP tool definitions
│   ├── cache/
│   │   └── kv.ts          # Cloudflare KV caching
│   └── types/
│       └── database.ts    # TypeScript interfaces for DB models
├── wrangler.toml          # Cloudflare config
└── package.json
```

### Direct Supabase Queries
**File**: `mcp-server/src/db/queries.ts`
```typescript
import { createClient } from '@supabase/supabase-js';

const supabase = createClient(env.SUPABASE_URL, env.SUPABASE_ANON_KEY);

export async function searchArticles(query: string, source?: string, limit = 20) {
  let queryBuilder = supabase
    .from('articles')
    .select('*')
    .or(`title.ilike.%${query}%,content.ilike.%${query}%`)
    .order('published_at', { ascending: false })
    .limit(limit);
  
  if (source) {
    queryBuilder = queryBuilder.eq('source', source);
  }
  
  const { data, error, count } = await queryBuilder;
  if (error) throw error;
  
  return { articles: data || [], total: count || 0 };
}

export async function getLatestArticles(hours = 24, source?: string, limit = 50) {
  const since = new Date(Date.now() - hours * 60 * 60 * 1000).toISOString();
  
  let queryBuilder = supabase
    .from('articles')
    .select('*')
    .gte('published_at', since)
    .order('published_at', { ascending: false })
    .limit(limit);
    
  if (source) {
    queryBuilder = queryBuilder.eq('source', source);
  }
  
  const { data, error } = await queryBuilder;
  if (error) throw error;
  
  return { articles: data || [], count: data?.length || 0, since };
}

export async function getArticleStats() {
  const { count: total } = await supabase
    .from('articles')
    .select('id', { count: 'exact', head: true });
    
  const { count: recent } = await supabase
    .from('articles')
    .select('id', { count: 'exact', head: true })
    .gte('published_at', new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString());
  
  return {
    total_articles: total || 0,
    recent_24h: recent || 0,
    last_updated: new Date().toISOString()
  };
}
```

### Methods to Port from ArticleRepository
1. `search_articles()` - ~30 lines
2. `get_articles()` - ~25 lines
3. `get_article_by_id()` - ~10 lines
4. `get_article_stats()` - ~20 lines
5. `get_digests()` - ~25 lines

**Total: ~110 lines of simple database queries**

---

## DEPLOYMENT & CONFIGURATION

### Cloudflare Configuration
**File**: `mcp-server/wrangler.toml`
```toml
name = "ai-news-mcp-server"
main = "src/index.ts"
compatibility_date = "2025-01-11"

[env.production]
kv_namespaces = [
  { binding = "CACHE", id = "your-kv-namespace-id" }
]

[[env.production.routes]]
pattern = "mcp.your-domain.com/*"
zone_id = "your-zone-id"

[build]
command = "npm run build"
```

### Environment Variables

**For Hybrid (Python Backend .env):**
```env
# Existing config
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_anon_key

# New MCP API config
MCP_API_KEYS=key1,key2,key3  # Comma-separated valid API keys
MCP_RATE_LIMIT=100  # Requests per minute
```

**For Pure TypeScript (via wrangler secret):**
```bash
wrangler secret put SUPABASE_URL
wrangler secret put SUPABASE_ANON_KEY
```

### Client Configuration
```json
{
  "mcpServers": {
    "ai-news": {
      "url": "https://mcp.your-domain.com",
      "auth": {
        "type": "github"
      }
    }
  }
}
```

---

## SECURITY ARCHITECTURE

### Database Security
- **Never Trust Clients**: Server mediates ALL database access
- **Read-Only Operations**: No write operations for public users
- **Query Validation**: Comprehensive SQL injection prevention
- **Input Sanitization**: Zod schemas for all inputs

### Authentication & Authorization

#### GitHub OAuth 2.0 (For Public Deployment):
```typescript
const PRIVILEGED_USERS = new Set(['your-github-username']);

export default new OAuthProvider({
  apiHandlers: {
    '/mcp': MyMCP.serve('/mcp'),
  },
  authorizeEndpoint: "/authorize",
  defaultHandler: GitHubHandler,
  tokenEndpoint: "/token",
});
```

### Input Validation
```typescript
const SearchContentSchema = z.object({
  query: z.string().min(1).max(200),
  source: z.enum(['arxiv', 'hackernews', 'rss']).optional(),
  limit: z.number().int().positive().max(50).default(10),
  category_filter: z.array(z.string()).max(5).optional()
});
```

### Rate Limiting
```typescript
const RATE_LIMITS = {
  content_search: { requests: 100, window: '1h' },
  export_articles: { requests: 5, window: '1d' },
  generate_summary: { requests: 50, window: '1h' }
};
```

---

## MCP TOOL TIERS

### MVP Tools (Week 1-2)
1. **Content Retrieval Tools**
   - `get_latest_articles`: Fetch recent AI/ML articles
   - `search_articles`: Search across all content
   - `get_article_by_id`: Retrieve specific article
   - `get_stats`: Database statistics

2. **Basic Analysis Tools**
   - `summarize_article`: Generate AI summaries
   - `get_daily_digest`: Latest daily digest
   - `get_trending_topics`: Trending topics analysis

### Tier 1: Advanced Tools (Month 2-3)
- `export_articles`: Export in JSON, CSV, Markdown formats
- `generate_report`: Comprehensive reports
- `analyze_trends`: Vector similarity trending

### Tier 2: Configuration (Month 3-4)
- `manage_feeds`: RSS feed management (Admin only)
- `system_health`: Monitor data sources (Admin only)

---

## IMPLEMENTATION TIMELINE

### Week 1: Foundation
- Choose architecture based on Python hosting status
- Set up basic project structure
- Implement authentication layer

### Week 2: Core Implementation
- For Hybrid: Create Python API endpoints + TypeScript proxy
- For Pure TS: Port database queries directly
- Add Cloudflare KV caching

### Week 3: Deployment
- Deploy to Cloudflare Workers
- Set up monitoring and analytics
- Create documentation

---

## MONITORING & OBSERVABILITY

### Required Metrics
- Error tracking (Sentry or similar)
- Performance monitoring (latency, throughput)
- User analytics (usage patterns)
- Security monitoring (failed auth, rate limits)

### Structured Logging
```typescript
console.log({
  timestamp: new Date().toISOString(),
  level: 'info',
  tool: toolName,
  user: props.login,
  duration_ms: executionTime,
  success: true
});
```

---

## DOCUMENTATION & RESOURCES

**MCP Protocol & SDKs:**
- Model Context Protocol specification: https://spec.modelcontextprotocol.io/
- MCP TypeScript SDK: https://github.com/modelcontextprotocol/typescript-sdk
- MCP Python SDK: https://github.com/modelcontextprotocol/python-sdk
- Claude MCP integration: https://docs.anthropic.com/en/docs/build-with-claude/mcp

**Deployment & Infrastructure:**
- Cloudflare Workers: https://developers.cloudflare.com/workers/
- Wrangler CLI: https://developers.cloudflare.com/workers/wrangler/
- GitHub OAuth: https://docs.github.com/en/developers/apps/oauth-apps
- Supabase: https://supabase.com/docs

**Security Best Practices:**
- OAuth 2.0: https://tools.ietf.org/html/rfc6749
- SQL injection prevention: https://owasp.org/www-community/attacks/SQL_Injection
- Rate limiting: https://blog.cloudflare.com/rate-limiting-with-cloudflare-workers/

---

## KEY CONSIDERATIONS

### MCP Protocol Compliance
- Follow MCP specification for tool definitions
- Use proper JSON-RPC 2.0 format
- Implement required server capabilities
- Handle client lifecycle properly

### Production Readiness
- Security first: validate all inputs
- Comprehensive error handling
- Performance monitoring
- Audit trail for all operations

### Testing Strategy
- MCP Inspector for development
- Unit tests for all tools
- Integration tests for protocol compliance
- Security penetration testing

### Portfolio Value
Regardless of architecture choice:
> "Evaluated hybrid and pure architectures, selecting [approach] based on infrastructure constraints and performance requirements, demonstrating architectural decision-making skills."

---

## FINAL RECOMMENDATION

**Decision Tree:**
```
Is Python backend already hosted publicly?
├─ YES → Use Hybrid Architecture
│   └─ Benefits: Code reuse, single source of truth
└─ NO → Use Pure TypeScript
    └─ Benefits: Zero cost, no cold starts, simpler

If unsure about future Python hosting?
└─ Start with Pure TypeScript
    └─ Can migrate to hybrid later if needed
```

This comprehensive plan provides everything needed to build a production-ready MCP server, with clear guidance on choosing between hybrid and pure TypeScript approaches based on your infrastructure situation.