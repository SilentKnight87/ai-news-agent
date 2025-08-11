# Project Requirement Plan: AI News Aggregator MCP Server Implementation

**Generated:** January 11, 2025  
**Agent Type:** backend-api-architect  
**Architecture Decision:** Pure TypeScript (Direct Supabase Connection)  
**Confidence Score:** 9/10

## Executive Summary

Extend the existing production-ready MCP server (Cloudflare Workers, TypeScript, GitHub OAuth) to expose AI news aggregator data and tools. The server already has secure database access, OAuth authentication, and tool registration infrastructure. We will add news-specific tools by porting key queries from the Python repository and implementing caching for optimal performance.

**Critical Context:** The Python backend is NOT deployed publicly, confirming Pure TypeScript architecture is correct. The existing MCP server in `mcp-server/` is well-architected with GitHub OAuth, SQL injection protection, and role-based access control.

## Architecture Overview

```
┌─────────────────────┐     ┌──────────────────────┐     ┌─────────────────────┐
│   MCP Clients       │────▶│  TypeScript MCP      │────▶│   Supabase          │
│ (Claude/Cursor/etc) │     │  (Cloudflare Workers)│     │   (PostgreSQL)      │
└─────────────────────┘     └──────────────────────┘     └─────────────────────┘
       MCP Protocol         Existing Infrastructure        Direct Connection
                           + New AI News Tools
```

## Pre-Implementation Research

### 1. Get Latest Documentation

```
# FastAPI docs (for reference patterns from Python code)
mcp__context7__resolve-library-id("fastapi")
mcp__context7__get-library-docs("/tiangolo/fastapi", topic="dependencies")

# Supabase client docs for TypeScript
mcp__context7__resolve-library-id("supabase-js")
mcp__context7__get-library-docs("/supabase/supabase-js", topic="select queries")

# Cloudflare Workers KV for caching
mcp__context7__resolve-library-id("cloudflare-workers")
mcp__context7__get-library-docs("/cloudflare/workers-types", topic="kv namespace")
```

### 2. Inspect Current Database Schema

```
mcp__supabase__list_tables(schemas=["public"])
mcp__supabase__execute_sql(query="SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'articles'")
mcp__supabase__execute_sql(query="SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'daily_digests'")
```

### 3. Web Research

Search for:
- "MCP server Cloudflare Workers best practices 2025" 
- "TypeScript Supabase connection pooling edge functions"
- "Cloudflare KV caching strategies for database queries"

## Implementation Blueprint

### Phase 1: Database Query Module

**File:** `mcp-server/src/database/news-queries.ts`

Port these methods from `src/repositories/articles.py`:

```typescript
import { getDb } from './connection';
import { validateSqlQuery } from './security';
import { withDatabase } from './utils';

export interface ArticleFilters {
  source?: string;
  limit?: number;
  offset?: number;
  since?: Date;
  minRelevanceScore?: number;
}

/**
 * Search articles using full-text search
 * Ported from: src/repositories/articles.py:search_articles()
 */
export async function searchArticles(
  databaseUrl: string, 
  query: string, 
  filters?: ArticleFilters
): Promise<{ articles: any[], total: number }> {
  return withDatabase(databaseUrl, async (db) => {
    // Build dynamic query similar to Python implementation
    const conditions = ['to_tsvector(title || \' \' || content) @@ plainto_tsquery($1)'];
    const params = [query];
    
    if (filters?.source) {
      conditions.push(`source = $${params.length + 1}`);
      params.push(filters.source);
    }
    
    if (filters?.minRelevanceScore) {
      conditions.push(`relevance_score >= $${params.length + 1}`);
      params.push(filters.minRelevanceScore);
    }
    
    const whereClause = conditions.join(' AND ');
    const limit = filters?.limit || 20;
    const offset = filters?.offset || 0;
    
    // Get total count
    const countResult = await db.unsafe(
      `SELECT COUNT(*) FROM articles WHERE ${whereClause}`,
      params
    );
    
    // Get paginated results
    const articles = await db.unsafe(
      `SELECT * FROM articles 
       WHERE ${whereClause}
       ORDER BY published_at DESC
       LIMIT ${limit} OFFSET ${offset}`,
      params
    );
    
    return { articles, total: parseInt(countResult[0].count) };
  });
}

/**
 * Get latest articles from past N hours
 * Ported from: src/repositories/articles.py:get_articles()
 */
export async function getLatestArticles(
  databaseUrl: string,
  hours = 24,
  filters?: ArticleFilters
): Promise<any[]> {
  return withDatabase(databaseUrl, async (db) => {
    const since = new Date(Date.now() - hours * 60 * 60 * 1000);
    
    let query = `
      SELECT * FROM articles 
      WHERE published_at >= $1
      AND is_duplicate = false
    `;
    const params: any[] = [since];
    
    if (filters?.source) {
      query += ` AND source = $${params.length + 1}`;
      params.push(filters.source);
    }
    
    query += ` ORDER BY published_at DESC LIMIT ${filters?.limit || 50}`;
    
    return db.unsafe(query, params);
  });
}

/**
 * Get article statistics
 * Ported from: src/repositories/articles.py:get_article_stats()
 */
export async function getArticleStats(databaseUrl: string): Promise<any> {
  return withDatabase(databaseUrl, async (db) => {
    const stats = await db.unsafe(`
      SELECT 
        COUNT(*) as total_articles,
        COUNT(CASE WHEN published_at > NOW() - INTERVAL '24 hours' THEN 1 END) as recent_24h,
        COUNT(CASE WHEN is_duplicate = true THEN 1 END) as duplicates,
        COUNT(DISTINCT source) as unique_sources,
        AVG(relevance_score) as avg_relevance
      FROM articles
    `);
    
    return stats[0];
  });
}

/**
 * Get daily digests with pagination
 * Ported from: src/repositories/articles.py:get_digests()
 */
export async function getDigests(
  databaseUrl: string,
  page = 1,
  perPage = 10
): Promise<{ digests: any[], total: number }> {
  return withDatabase(databaseUrl, async (db) => {
    const offset = (page - 1) * perPage;
    
    const countResult = await db.unsafe(
      'SELECT COUNT(*) FROM daily_digests'
    );
    
    const digests = await db.unsafe(`
      SELECT 
        id, date, title, summary, key_developments,
        audio_url, audio_duration, created_at,
        (SELECT COUNT(*) FROM digest_articles WHERE digest_id = daily_digests.id) as article_count
      FROM daily_digests
      ORDER BY date DESC
      LIMIT $1 OFFSET $2
    `, [perPage, offset]);
    
    return { 
      digests, 
      total: parseInt(countResult[0].count) 
    };
  });
}

/**
 * Get single digest with articles
 * Ported from: src/repositories/articles.py:get_digest_by_id()
 */
export async function getDigestById(
  databaseUrl: string,
  digestId: string
): Promise<any> {
  return withDatabase(databaseUrl, async (db) => {
    const digest = await db.unsafe(`
      SELECT * FROM daily_digests WHERE id = $1
    `, [digestId]);
    
    if (!digest.length) return null;
    
    const articles = await db.unsafe(`
      SELECT a.* 
      FROM articles a
      JOIN digest_articles da ON a.id = da.article_id
      WHERE da.digest_id = $1
      ORDER BY a.relevance_score DESC
    `, [digestId]);
    
    return { ...digest[0], articles };
  });
}

/**
 * Get sources metadata
 * New function for MCP server
 */
export async function getSourcesMetadata(databaseUrl: string): Promise<any[]> {
  return withDatabase(databaseUrl, async (db) => {
    const sources = await db.unsafe(`
      SELECT 
        source as name,
        COUNT(*) as article_count,
        MAX(published_at) as last_published,
        AVG(relevance_score) as avg_relevance_score,
        COUNT(CASE WHEN published_at > NOW() - INTERVAL '7 days' THEN 1 END) as recent_count
      FROM articles
      GROUP BY source
      ORDER BY article_count DESC
    `);
    
    // Add display names and descriptions
    return sources.map(source => ({
      ...source,
      display_name: getSourceDisplayName(source.name),
      description: getSourceDescription(source.name),
      status: source.recent_count > 0 ? 'active' : 'inactive'
    }));
  });
}

// Helper functions
function getSourceDisplayName(source: string): string {
  const displayNames: Record<string, string> = {
    'arxiv': 'ArXiv',
    'hackernews': 'Hacker News',
    'reddit_machinelearning': 'Reddit r/MachineLearning',
    'reddit_locallama': 'Reddit r/LocalLLaMA',
    'github_trending': 'GitHub Trending'
  };
  return displayNames[source] || source;
}

function getSourceDescription(source: string): string {
  const descriptions: Record<string, string> = {
    'arxiv': 'Latest AI/ML research papers',
    'hackernews': 'Tech news and discussions',
    'reddit_machinelearning': 'ML community discussions',
    'reddit_locallama': 'Open source LLM discussions',
    'github_trending': 'Trending AI/ML repositories'
  };
  return descriptions[source] || 'AI/ML news source';
}
```

### Phase 2: Tool Registration

**File:** `mcp-server/src/tools/news-tools.ts`

```typescript
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";
import { Props } from "../types";
import * as newsQueries from '../database/news-queries';

// Input validation schemas
const SearchArticlesSchema = z.object({
  query: z.string().min(1).max(200).describe("Search query"),
  source: z.string().optional().describe("Filter by source (arxiv, hackernews, reddit_machinelearning, etc)"),
  limit: z.number().int().positive().max(100).default(20).describe("Number of results"),
  offset: z.number().int().min(0).default(0).describe("Pagination offset")
});

const GetLatestArticlesSchema = z.object({
  hours: z.number().int().positive().max(168).default(24).describe("Get articles from past N hours"),
  source: z.string().optional().describe("Filter by source"),
  limit: z.number().int().positive().max(100).default(50).describe("Number of results")
});

const GetDigestsSchema = z.object({
  page: z.number().int().positive().default(1).describe("Page number"),
  per_page: z.number().int().positive().max(50).default(10).describe("Items per page")
});

const GetDigestByIdSchema = z.object({
  digest_id: z.string().uuid().describe("Digest UUID")
});

export function registerNewsTools(server: McpServer, env: Env, props: Props) {
  console.log(`Registering news tools for user: ${props.login}`);

  // Tool 1: Search Articles
  server.tool(
    "search_articles",
    "Search AI/ML news articles using full-text search. Returns articles matching the query with relevance scores.",
    SearchArticlesSchema,
    async ({ query, source, limit, offset }) => {
      try {
        const startTime = Date.now();
        
        // Check cache first
        const cacheKey = `search:${query}:${source}:${limit}:${offset}`;
        const cached = await env.CACHE?.get(cacheKey, "json");
        if (cached) {
          return {
            content: [{
              type: "text",
              text: `**Cached Search Results**\n\nQuery: "${query}"\n${cached.total} total results\n\n\`\`\`json\n${JSON.stringify(cached.articles, null, 2)}\n\`\`\``
            }]
          };
        }
        
        // Execute search
        const result = await newsQueries.searchArticles(
          env.DATABASE_URL,
          query,
          { source, limit, offset }
        );
        
        // Cache for 5 minutes
        await env.CACHE?.put(cacheKey, JSON.stringify(result), { expirationTtl: 300 });
        
        const duration = Date.now() - startTime;
        
        return {
          content: [{
            type: "text",
            text: `**Search Results**\n\nQuery: "${query}"\n${result.total} total results\nDuration: ${duration}ms\n\n\`\`\`json\n${JSON.stringify(result.articles, null, 2)}\n\`\`\``
          }]
        };
      } catch (error) {
        console.error("Search articles error:", error);
        return {
          content: [{
            type: "text",
            text: `**Error**\n\nFailed to search articles: ${error instanceof Error ? error.message : String(error)}`,
            isError: true
          }]
        };
      }
    }
  );

  // Tool 2: Get Latest Articles
  server.tool(
    "get_latest_articles",
    "Get the most recent AI/ML news articles from the past N hours. Default is 24 hours.",
    GetLatestArticlesSchema,
    async ({ hours, source, limit }) => {
      try {
        const cacheKey = `latest:${hours}:${source}:${limit}`;
        const cached = await env.CACHE?.get(cacheKey, "json");
        if (cached) {
          return {
            content: [{
              type: "text",
              text: `**Cached Latest Articles**\n\nFrom past ${hours} hours\n${cached.length} articles\n\n\`\`\`json\n${JSON.stringify(cached, null, 2)}\n\`\`\``
            }]
          };
        }
        
        const articles = await newsQueries.getLatestArticles(
          env.DATABASE_URL,
          hours,
          { source, limit }
        );
        
        // Cache for 10 minutes
        await env.CACHE?.put(cacheKey, JSON.stringify(articles), { expirationTtl: 600 });
        
        return {
          content: [{
            type: "text",
            text: `**Latest Articles**\n\nFrom past ${hours} hours\n${articles.length} articles found\n\n\`\`\`json\n${JSON.stringify(articles, null, 2)}\n\`\`\``
          }]
        };
      } catch (error) {
        console.error("Get latest articles error:", error);
        return {
          content: [{
            type: "text",
            text: `**Error**\n\nFailed to get latest articles: ${error instanceof Error ? error.message : String(error)}`,
            isError: true
          }]
        };
      }
    }
  );

  // Tool 3: Get Statistics
  server.tool(
    "get_article_stats",
    "Get comprehensive statistics about the AI news database including total articles, sources, and trends.",
    {},
    async () => {
      try {
        const stats = await newsQueries.getArticleStats(env.DATABASE_URL);
        
        return {
          content: [{
            type: "text",
            text: `**Database Statistics**\n\n• Total Articles: ${stats.total_articles}\n• Last 24 Hours: ${stats.recent_24h}\n• Duplicates: ${stats.duplicates}\n• Unique Sources: ${stats.unique_sources}\n• Average Relevance: ${Math.round(stats.avg_relevance)}%\n\n\`\`\`json\n${JSON.stringify(stats, null, 2)}\n\`\`\``
          }]
        };
      } catch (error) {
        console.error("Get stats error:", error);
        return {
          content: [{
            type: "text",
            text: `**Error**\n\nFailed to get statistics: ${error instanceof Error ? error.message : String(error)}`,
            isError: true
          }]
        };
      }
    }
  );

  // Tool 4: Get Daily Digests
  server.tool(
    "get_digests",
    "Get paginated list of daily AI news digests with summaries and key developments.",
    GetDigestsSchema,
    async ({ page, per_page }) => {
      try {
        const result = await newsQueries.getDigests(
          env.DATABASE_URL,
          page,
          per_page
        );
        
        const totalPages = Math.ceil(result.total / per_page);
        
        return {
          content: [{
            type: "text",
            text: `**Daily Digests**\n\nPage ${page} of ${totalPages}\nTotal: ${result.total} digests\n\n\`\`\`json\n${JSON.stringify(result.digests, null, 2)}\n\`\`\``
          }]
        };
      } catch (error) {
        console.error("Get digests error:", error);
        return {
          content: [{
            type: "text",
            text: `**Error**\n\nFailed to get digests: ${error instanceof Error ? error.message : String(error)}`,
            isError: true
          }]
        };
      }
    }
  );

  // Tool 5: Get Single Digest
  server.tool(
    "get_digest_by_id",
    "Get a specific daily digest with all its articles and detailed information.",
    GetDigestByIdSchema,
    async ({ digest_id }) => {
      try {
        const digest = await newsQueries.getDigestById(
          env.DATABASE_URL,
          digest_id
        );
        
        if (!digest) {
          return {
            content: [{
              type: "text",
              text: `**Error**\n\nDigest not found with ID: ${digest_id}`,
              isError: true
            }]
          };
        }
        
        return {
          content: [{
            type: "text",
            text: `**Daily Digest**\n\n${digest.title}\nDate: ${digest.date}\nArticles: ${digest.articles.length}\n\n**Summary:**\n${digest.summary}\n\n**Articles:**\n\`\`\`json\n${JSON.stringify(digest.articles, null, 2)}\n\`\`\``
          }]
        };
      } catch (error) {
        console.error("Get digest by ID error:", error);
        return {
          content: [{
            type: "text",
            text: `**Error**\n\nFailed to get digest: ${error instanceof Error ? error.message : String(error)}`,
            isError: true
          }]
        };
      }
    }
  );

  // Tool 6: Get Sources Metadata
  server.tool(
    "get_sources",
    "Get metadata about all AI news sources including article counts and activity status.",
    {},
    async () => {
      try {
        const sources = await newsQueries.getSourcesMetadata(env.DATABASE_URL);
        
        const activeSources = sources.filter(s => s.status === 'active').length;
        
        return {
          content: [{
            type: "text",
            text: `**News Sources**\n\nTotal: ${sources.length} sources\nActive: ${activeSources} sources\n\n\`\`\`json\n${JSON.stringify(sources, null, 2)}\n\`\`\``
          }]
        };
      } catch (error) {
        console.error("Get sources error:", error);
        return {
          content: [{
            type: "text",
            text: `**Error**\n\nFailed to get sources: ${error instanceof Error ? error.message : String(error)}`,
            isError: true
          }]
        };
      }
    }
  );

  console.log(`Registered 6 news tools for user: ${props.login}`);
}
```

### Phase 3: Integration with Existing System

**File:** `mcp-server/src/tools/register-tools.ts` (UPDATE EXISTING)

```typescript
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { Props } from "../types";
// Existing imports...
import { registerDatabaseTools } from "../../examples/database-tools";
import { registerNewsTools } from "./news-tools"; // NEW

export function registerAllTools(server: McpServer, env: Env, props: Props) {
  // Existing database tools
  registerDatabaseTools(server, env, props);
  
  // NEW: Register AI news aggregator tools
  registerNewsTools(server, env, props);
  
  // Future tools can be registered here
  console.log(`All tools registered for user: ${props.login}`);
}
```

### Phase 4: Environment Configuration

**File:** `mcp-server/.dev.vars` (UPDATE)

```env
# Existing variables
GITHUB_CLIENT_ID=your_existing_id
GITHUB_CLIENT_SECRET=your_existing_secret
COOKIE_ENCRYPTION_KEY=your_existing_key
DATABASE_URL=postgresql://user:pass@host/db
SENTRY_DSN=your_sentry_dsn

# NEW: Add Supabase configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
```

**File:** `mcp-server/wrangler.jsonc` (UPDATE KV NAMESPACE)

```jsonc
{
  "name": "ai-news-mcp-server",
  "main": "src/index.ts",
  // ... existing config ...
  
  "kv_namespaces": [
    {
      "binding": "OAUTH_KV",
      "id": "existing-oauth-kv-id"
    },
    {
      "binding": "CACHE",  // NEW: Add cache namespace
      "id": "create-new-kv-namespace-id"
    }
  ]
}
```

### Phase 5: Caching Strategy

**File:** `mcp-server/src/cache/strategy.ts`

```typescript
export interface CacheConfig {
  searchArticles: { ttl: 300 };      // 5 minutes
  latestArticles: { ttl: 600 };      // 10 minutes  
  articleStats: { ttl: 3600 };       // 1 hour
  digests: { ttl: 3600 };            // 1 hour
  sources: { ttl: 86400 };           // 24 hours
}

export class CacheManager {
  constructor(private kv: KVNamespace) {}
  
  generateKey(operation: string, params: any): string {
    return `${operation}:${JSON.stringify(params)}`;
  }
  
  async get<T>(key: string): Promise<T | null> {
    const value = await this.kv.get(key, "json");
    return value as T;
  }
  
  async set(key: string, value: any, ttlSeconds: number): Promise<void> {
    await this.kv.put(key, JSON.stringify(value), {
      expirationTtl: ttlSeconds
    });
  }
  
  async invalidatePattern(pattern: string): Promise<void> {
    // List all keys matching pattern and delete
    const list = await this.kv.list({ prefix: pattern });
    for (const key of list.keys) {
      await this.kv.delete(key.name);
    }
  }
}
```

## Testing Strategy

### Unit Tests

**File:** `mcp-server/tests/tools/news-tools.test.ts`

```typescript
import { describe, it, expect, vi } from 'vitest';
import { registerNewsTools } from '../../src/tools/news-tools';
import * as newsQueries from '../../src/database/news-queries';

vi.mock('../../src/database/news-queries');

describe('News Tools', () => {
  it('should search articles with proper caching', async () => {
    const mockResults = { articles: [], total: 0 };
    vi.mocked(newsQueries.searchArticles).mockResolvedValue(mockResults);
    
    // Test implementation
  });
  
  it('should handle database errors gracefully', async () => {
    vi.mocked(newsQueries.searchArticles).mockRejectedValue(
      new Error('Database connection failed')
    );
    
    // Test error handling
  });
});
```

### MCP Inspector Testing

```bash
# Local testing with MCP Inspector
npx @modelcontextprotocol/inspector@latest

# Test each tool:
# 1. search_articles with query "LLM"
# 2. get_latest_articles with hours=24
# 3. get_article_stats
# 4. get_digests with page=1
# 5. get_sources
```

## Validation Gates

```bash
# 1. TypeScript compilation
npm run type-check

# 2. Unit tests
npm test

# 3. Wrangler validation
wrangler deploy --dry-run

# 4. Database schema validation (via MCP)
mcp__supabase__get_advisors(type="security")  # Check for missing RLS policies
mcp__supabase__get_advisors(type="performance")  # Check for missing indexes

# 5. Local development testing
wrangler dev
# Then test with curl:
curl http://localhost:8792/mcp \
  -H "Authorization: Bearer test-token" \
  -d '{"method": "tools/list"}'
```

## Performance Optimizations

1. **Connection Pooling**: Already implemented with max 5 connections
2. **KV Caching**: Cache expensive queries for 5-60 minutes
3. **Query Optimization**: Use indexes on `published_at`, `source`, `relevance_score`
4. **Pagination**: Limit default results to 20-50 items
5. **Edge Computing**: Cloudflare Workers run at edge locations globally

## Security Considerations

1. **SQL Injection**: Use existing `validateSqlQuery()` from `database/security.ts`
2. **Input Validation**: Zod schemas on all tool inputs
3. **Rate Limiting**: Cloudflare provides automatic DDoS protection
4. **Authentication**: GitHub OAuth already implemented
5. **Authorization**: Keep write operations limited to ALLOWED_USERNAMES

## Deployment Instructions

```bash
# 1. Install dependencies
cd mcp-server
npm install

# 2. Create KV namespace for caching
wrangler kv:namespace create "CACHE"
# Copy the ID to wrangler.jsonc

# 3. Set production secrets
wrangler secret put DATABASE_URL
wrangler secret put SUPABASE_URL
wrangler secret put SUPABASE_ANON_KEY

# 4. Deploy to Cloudflare
wrangler deploy

# 5. Test production endpoint
curl https://your-worker.workers.dev/mcp \
  -H "Authorization: Bearer your-token"
```

## MCP Client Configuration

**For Claude Desktop:**
```json
{
  "mcpServers": {
    "ai-news": {
      "command": "npx",
      "args": ["mcp-remote", "https://your-worker.workers.dev/mcp"],
      "env": {}
    }
  }
}
```

## Monitoring & Observability

1. **Cloudflare Analytics**: Built-in request metrics
2. **Sentry Integration**: Already configured in `index_sentry.ts`
3. **Structured Logging**: Log tool usage, errors, performance
4. **KV Analytics**: Monitor cache hit rates

## Common Issues & Solutions

1. **Database Connection Errors**
   - Check DATABASE_URL is correctly set
   - Verify Supabase allows connections from Cloudflare IPs
   
2. **OAuth Issues**
   - Ensure GitHub OAuth app callback URL matches Worker URL
   
3. **Performance Issues**
   - Check KV cache is working (monitor hit rates)
   - Review slow queries with `mcp__supabase__get_logs(service="postgres")`

## Success Metrics

- [ ] All 6 news tools successfully registered
- [ ] Cache hit rate > 50% after warm-up
- [ ] Average response time < 500ms
- [ ] Zero SQL injection vulnerabilities
- [ ] Successfully tested with Claude Desktop

## Documentation Links

- MCP Protocol: https://spec.modelcontextprotocol.io/
- Cloudflare Workers: https://developers.cloudflare.com/workers/
- Supabase TypeScript Client: https://supabase.com/docs/reference/javascript/introduction
- Existing MCP Server Docs: See `mcp-server/CLAUDE.md`

## Agent Instructions

**To: backend-api-architect agent**

You are extending an existing, production-ready MCP server. DO NOT rebuild from scratch. The authentication, database connection, and tool registration systems already work perfectly.

Your task:
1. Port the SQL queries from Python to TypeScript (see Phase 1)
2. Create news-specific tools following existing patterns (see Phase 2)
3. Add tools to the registration system (see Phase 3)
4. Implement KV caching for performance (see Phase 5)
5. Write comprehensive tests

Use the existing patterns from `examples/database-tools.ts` as your template. The database connection, security validation, and error handling are already implemented - just use them.

Remember: This is a PUBLIC MCP server. No write operations for regular users. Only read operations are allowed.

---

**Confidence Score: 9/10**

This PRP provides comprehensive guidance for implementing AI news aggregator tools on top of the existing MCP server infrastructure. The existing codebase is well-architected, so success probability is very high by following these patterns.