# PRP: Frontend Direct Supabase Access Migration

## Executive Summary
Migrate the AI News Aggregator frontend from API-dependent architecture to direct Supabase database access using Row Level Security (RLS). This eliminates the need for a backend API server while maintaining security and improving performance.

**Target Completion:** Single-pass implementation using Claude Code with MCP tools
**Confidence Score:** 9/10 - Comprehensive context with clear implementation path

## Context & Background

### Current Architecture Problems
- **Missing API Server**: Frontend expects API at `/api/*` but no backend exists
- **Deployment Blocked**: Frontend cannot function without data access
- **Unnecessary Complexity**: API layer adds latency and maintenance overhead

### Target Architecture Benefits
- **Zero Infrastructure**: No API server to deploy or maintain
- **Sub-50ms Response Times**: Direct connection via Supabase global CDN
- **Type Safety**: Auto-generated TypeScript types from database schema
- **Real-time Capabilities**: Built-in subscriptions for live updates
- **Industry Standard**: JAMstack pattern used by modern SaaS products

### Existing Codebase Analysis
- **Frontend Stack**: Next.js 15.4.5, React 18.2, TypeScript 5, TailwindCSS
- **Data Fetching**: SWR 2.3.4 for caching and revalidation
- **Current API Client**: Located at `UI/src/lib/api.ts` (to be replaced)
- **Hooks Pattern**: Existing hooks in `UI/src/hooks/*.ts` use SWR
- **Type Definitions**: `UI/src/types/index.ts` defines Article, Digest, Stats interfaces

### Database Schema Reference
```sql
-- Articles table with pgvector embedding
CREATE TABLE articles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id TEXT NOT NULL,
    source article_source NOT NULL, -- enum type
    title VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,
    url TEXT NOT NULL,
    author TEXT,
    published_at TIMESTAMP WITH TIME ZONE NOT NULL,
    fetched_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    summary TEXT,
    relevance_score REAL,
    categories TEXT[] DEFAULT '{}',
    key_points TEXT[] DEFAULT '{}',
    embedding vector(384), -- pgvector for similarity search
    is_duplicate BOOLEAN DEFAULT FALSE,
    duplicate_of UUID REFERENCES articles(id),
    UNIQUE(source, source_id)
);

-- Daily digests table
CREATE TABLE daily_digests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    digest_date DATE NOT NULL UNIQUE,
    summary_text TEXT NOT NULL,
    total_articles_processed INTEGER NOT NULL,
    audio_url TEXT,
    audio_duration INTEGER,
    audio_size INTEGER,
    voice_type VARCHAR(50) DEFAULT 'news',
    audio_generated_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Junction table for many-to-many relationship
CREATE TABLE digest_articles (
    digest_id UUID REFERENCES daily_digests(id),
    article_id UUID REFERENCES articles(id),
    PRIMARY KEY (digest_id, article_id)
);
```

## Pre-Implementation Research

### 1. Get Latest Supabase Client Documentation
Use Context7 MCP to fetch current docs:
```
mcp__context7__resolve-library-id("@supabase/supabase-js")
mcp__context7__get-library-docs("/supabase/supabase-js", topic="nextjs client initialization")
mcp__context7__get-library-docs("/supabase/supabase-js", topic="typescript types generation")
```

### 2. Inspect Current Database Schema
Use Supabase MCP to verify schema:
```
mcp__supabase__list_tables(schemas=["public"])
mcp__supabase__execute_sql("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'articles'")
mcp__supabase__execute_sql("SELECT enum_range(NULL::article_source)")
```

### 3. Check for Missing Enum Values
Verify and add missing source types if needed:
```sql
-- Check existing enum values
SELECT unnest(enum_range(NULL::article_source)) AS source_type;

-- Add missing values if needed (execute via Supabase MCP)
ALTER TYPE article_source ADD VALUE IF NOT EXISTS 'youtube';
ALTER TYPE article_source ADD VALUE IF NOT EXISTS 'huggingface';
ALTER TYPE article_source ADD VALUE IF NOT EXISTS 'reddit';
ALTER TYPE article_source ADD VALUE IF NOT EXISTS 'github';
```

## Implementation Blueprint

### Phase 1: Setup Supabase Client (Priority: Critical)

#### 1.1 Install Dependencies
```bash
cd UI
npm install @supabase/supabase-js@^2.39.0
npm install @types/node --save-dev
```

#### 1.2 Create Supabase Client Configuration
Create `UI/src/lib/supabase.ts`:
```typescript
import { createClient } from '@supabase/supabase-js'
import { Database } from '@/types/database'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!

if (!supabaseUrl || !supabaseAnonKey) {
  throw new Error('Missing Supabase environment variables')
}

export const supabase = createClient<Database>(supabaseUrl, supabaseAnonKey, {
  auth: {
    persistSession: false, // Anonymous access only
  },
  db: {
    schema: 'public',
  },
  global: {
    headers: {
      'x-application-name': 'ai-news-frontend',
    },
  },
})

export type SupabaseClient = typeof supabase
```

#### 1.3 Environment Variables Setup
Create `UI/.env.local`:
```env
NEXT_PUBLIC_SUPABASE_URL=<get_from_supabase_dashboard>
NEXT_PUBLIC_SUPABASE_ANON_KEY=<get_from_supabase_dashboard>
```

**MCP Tool Usage:**
```
mcp__supabase__get_project_url()  # Get the Supabase URL
mcp__supabase__get_anon_key()     # Get the anon key
```

### Phase 2: Configure Row Level Security (Priority: Critical)

#### 2.1 Enable RLS on Tables
Use Supabase MCP to execute:
```sql
-- Enable RLS
ALTER TABLE articles ENABLE ROW LEVEL SECURITY;
ALTER TABLE daily_digests ENABLE ROW LEVEL SECURITY;
ALTER TABLE digest_articles ENABLE ROW LEVEL SECURITY;

-- Create read-only policies for anonymous access
CREATE POLICY "Frontend anonymous read articles" ON articles
FOR SELECT TO anon USING (true);

CREATE POLICY "Frontend anonymous read digests" ON daily_digests
FOR SELECT TO anon USING (true);

CREATE POLICY "Frontend anonymous read digest_articles" ON digest_articles
FOR SELECT TO anon USING (true);
```

#### 2.2 Verify RLS Configuration
Test policies via Supabase MCP:
```sql
-- Test as anonymous user
SET ROLE anon;
SELECT COUNT(*) FROM articles;
SELECT COUNT(*) FROM daily_digests;

-- Verify write operations are blocked
INSERT INTO articles (title, content, url, source, source_id, published_at)
VALUES ('test', 'test', 'test', 'arxiv', 'test', NOW());
-- Should fail with permission denied

RESET ROLE;
```

### Phase 3: Generate TypeScript Types (Priority: High)

#### 3.1 Auto-generate Types from Schema
Use Supabase MCP:
```
mcp__supabase__generate_typescript_types()
```

Save output to `UI/src/types/database.ts`

#### 3.2 Create Type Transformers
Create `UI/src/lib/transformers.ts`:
```typescript
import { Database } from '@/types/database'
import { Article, Digest, Stats } from '@/types'

type ArticleRow = Database['public']['Tables']['articles']['Row']
type DigestRow = Database['public']['Tables']['daily_digests']['Row']

export function transformArticleRow(row: ArticleRow): Article {
  return {
    id: row.id,
    title: row.title,
    url: row.url,
    source: row.source,
    summary: row.summary || '',
    relevance_score: row.relevance_score || 0,
    categories: row.categories || [],
    published_at: row.published_at,
    created_at: row.fetched_at,
    updated_at: row.fetched_at,
    author: row.author || undefined,
    content: row.content,
    tags: row.key_points || [],
  }
}

export function transformDigestRow(row: DigestRow, articles: Article[] = []): Digest {
  return {
    id: row.id,
    title: `Daily Digest - ${new Date(row.digest_date).toLocaleDateString()}`,
    summary: row.summary_text,
    key_points: [],
    audio_url: row.audio_url || '',
    duration: row.audio_duration || 0,
    articles,
    created_at: row.created_at,
  }
}
```

### Phase 4: Implement Query Service (Priority: Critical)

Create `UI/src/lib/supabase-queries.ts`:
```typescript
import { supabase } from './supabase'
import { Database } from '@/types/database'
import { Article, ArticleFilters, Digest, Stats, PaginationMeta } from '@/types'
import { transformArticleRow, transformDigestRow } from './transformers'

export const supabaseQueries = {
  // Articles with filtering and pagination
  async getArticles(filters: ArticleFilters & { page?: number; per_page?: number } = {}) {
    const { source, category, relevance_min, time_range, page = 1, per_page = 20 } = filters

    let query = supabase
      .from('articles')
      .select('*', { count: 'exact' })
      .eq('is_duplicate', false)
      .order('published_at', { ascending: false })

    // Apply filters
    if (source) query = query.eq('source', source)
    if (category) query = query.contains('categories', [category])
    if (relevance_min !== undefined) query = query.gte('relevance_score', relevance_min)
    
    if (time_range) {
      const now = new Date()
      let startDate: Date
      switch (time_range) {
        case '24h':
          startDate = new Date(now.getTime() - 24 * 60 * 60 * 1000)
          break
        case '7d':
          startDate = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000)
          break
        case '30d':
          startDate = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000)
          break
        default:
          startDate = new Date(now.getTime() - 24 * 60 * 60 * 1000)
      }
      query = query.gte('published_at', startDate.toISOString())
    }

    // Pagination
    const from = (page - 1) * per_page
    const to = from + per_page - 1
    query = query.range(from, to)

    const { data, error, count } = await query

    if (error) throw new Error(`Failed to fetch articles: ${error.message}`)

    const articles = data?.map(transformArticleRow) || []
    const total = count || 0
    const total_pages = Math.ceil(total / per_page)

    return {
      articles,
      pagination: {
        page,
        per_page,
        total,
        total_pages,
        has_next: page < total_pages,
        has_prev: page > 1,
      } as PaginationMeta,
      meta: {
        sort_by: 'published_at' as const,
        order: 'desc' as const,
        cache_hit: false,
      }
    }
  },

  // Get single article
  async getArticle(id: string): Promise<Article> {
    const { data, error } = await supabase
      .from('articles')
      .select('*')
      .eq('id', id)
      .single()

    if (error) throw new Error(`Failed to fetch article: ${error.message}`)
    if (!data) throw new Error('Article not found')

    return transformArticleRow(data)
  },

  // Search articles with fallback
  async searchArticles(query: string, options: { limit?: number; offset?: number } = {}) {
    const { limit = 20, offset = 0 } = options

    // Try full-text search first
    const { data, error } = await supabase
      .rpc('search_articles_fulltext', {
        query_text: query,
        max_results: limit,
        skip_results: offset
      })

    if (error) {
      // Fallback to ILIKE search
      console.warn('Using fallback search:', error.message)
      const fallback = await supabase
        .from('articles')
        .select('*', { count: 'exact' })
        .or(`title.ilike.%${query}%,content.ilike.%${query}%,summary.ilike.%${query}%`)
        .eq('is_duplicate', false)
        .order('relevance_score', { ascending: false, nullsLast: true })
        .range(offset, offset + limit - 1)

      if (fallback.error) throw new Error(`Search failed: ${fallback.error.message}`)

      return {
        articles: fallback.data?.map(transformArticleRow) || [],
        total: fallback.count || 0,
        query,
        took_ms: 0,
      }
    }

    return {
      articles: data?.map(transformArticleRow) || [],
      total: data?.[0]?.total_count || 0,
      query,
      took_ms: 0,
    }
  },

  // Get similar articles using pgvector
  async getSimilarArticles(articleId: string, options: { limit?: number; threshold?: number } = {}) {
    const { limit = 5, threshold = 0.85 } = options

    // Get target article embedding
    const { data: article, error: articleError } = await supabase
      .from('articles')
      .select('embedding')
      .eq('id', articleId)
      .single()

    if (articleError || !article?.embedding) {
      throw new Error('Article not found or has no embedding')
    }

    // Use vector similarity search
    const { data, error } = await supabase
      .rpc('match_articles', {
        query_embedding: article.embedding,
        match_threshold: threshold,
        match_count: limit
      })

    if (error) throw new Error(`Similarity search failed: ${error.message}`)

    return {
      articles: data?.map((item: any) => ({
        id: item.id,
        title: item.title,
        url: item.url,
        similarity: item.similarity,
        published_at: item.published_at
      })) || [],
      query_article_id: articleId,
      threshold,
    }
  },

  // Get latest digest with articles
  async getLatestDigest(): Promise<Digest | null> {
    const { data, error } = await supabase
      .from('daily_digests')
      .select(`
        *,
        digest_articles!inner(
          articles(*)
        )
      `)
      .order('digest_date', { ascending: false })
      .limit(1)
      .single()

    if (error && error.code !== 'PGRST116') { // PGRST116 = no rows
      throw new Error(`Failed to fetch latest digest: ${error.message}`)
    }

    if (!data) return null

    const articles = (data.digest_articles as any[])
      ?.map((da: any) => da.articles)
      ?.filter(Boolean)
      ?.map(transformArticleRow) || []

    return transformDigestRow(data, articles)
  },

  // Get statistics
  async getStats(): Promise<Stats> {
    // Parallel queries for performance
    const [totalResult, sourceResult, categoryResult, last24hResult, lastWeekResult] = await Promise.all([
      supabase.from('articles').select('*', { count: 'exact', head: true }).eq('is_duplicate', false),
      supabase.from('articles').select('source').eq('is_duplicate', false),
      supabase.from('articles').select('categories').eq('is_duplicate', false).not('categories', 'is', null),
      supabase.from('articles').select('*', { count: 'exact', head: true })
        .eq('is_duplicate', false)
        .gte('published_at', new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString()),
      supabase.from('articles').select('*', { count: 'exact', head: true })
        .eq('is_duplicate', false)
        .gte('published_at', new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString()),
    ])

    // Aggregate source counts
    const articles_by_source: Record<string, number> = {}
    sourceResult.data?.forEach(item => {
      articles_by_source[item.source] = (articles_by_source[item.source] || 0) + 1
    })

    // Aggregate category counts
    const articles_by_category: Record<string, number> = {}
    categoryResult.data?.forEach(item => {
      item.categories?.forEach(category => {
        articles_by_category[category] = (articles_by_category[category] || 0) + 1
      })
    })

    return {
      total_articles: totalResult.count || 0,
      articles_by_source,
      articles_by_category,
      avg_relevance_score: 0, // Calculate if needed
      articles_last_24h: last24hResult.count || 0,
      articles_last_week: lastWeekResult.count || 0,
    }
  }
}
```

### Phase 5: Update React Hooks (Priority: High)

Update `UI/src/hooks/useArticles.ts`:
```typescript
import useSWR from 'swr'
import { supabaseQueries } from '@/lib/supabase-queries'
import { ArticleFilters } from '@/types'

export function useArticles(source?: string, filters?: ArticleFilters) {
  const key = source ? ['articles', source, filters] : ['articles', filters]
  return useSWR(key, () => supabaseQueries.getArticles({ source, ...filters }))
}

export function useArticle(id: string) {
  return useSWR(id ? ['article', id] : null, () => supabaseQueries.getArticle(id))
}

export function useDigest() {
  return useSWR('digest', supabaseQueries.getLatestDigest, {
    refreshInterval: 60000,
  })
}

export function useStats() {
  return useSWR('stats', supabaseQueries.getStats, {
    refreshInterval: 30000,
  })
}

export function useSearch(query: string, options?: { limit?: number; offset?: number }) {
  return useSWR(
    query ? ['search', query, options] : null,
    () => supabaseQueries.searchArticles(query, options),
    { revalidateOnFocus: false, dedupingInterval: 5000 }
  )
}
```

### Phase 6: Database Optimization (Priority: Medium)

Create indexes via Supabase MCP:
```sql
-- Performance indexes
CREATE INDEX IF NOT EXISTS idx_articles_published_at_desc ON articles(published_at DESC);
CREATE INDEX IF NOT EXISTS idx_articles_source_published ON articles(source, published_at DESC);
CREATE INDEX IF NOT EXISTS idx_articles_relevance_score ON articles(relevance_score DESC) WHERE relevance_score IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_articles_categories_gin ON articles USING gin(categories);

-- Text search indexes
CREATE INDEX IF NOT EXISTS idx_articles_title_gin ON articles USING gin(to_tsvector('english', title));
CREATE INDEX IF NOT EXISTS idx_articles_content_gin ON articles USING gin(to_tsvector('english', content));

-- Digest indexes
CREATE INDEX IF NOT EXISTS idx_digests_date_desc ON daily_digests(digest_date DESC);
CREATE INDEX IF NOT EXISTS idx_digest_articles_digest_id ON digest_articles(digest_id);
```

### Phase 7: Error Handling & Loading States (Priority: Medium)

Update `UI/src/components/ErrorBoundary.tsx`:
```typescript
import React from 'react'

interface ErrorBoundaryState {
  hasError: boolean
  error?: Error
}

export class ErrorBoundary extends React.Component<
  React.PropsWithChildren<{}>,
  ErrorBoundaryState
> {
  constructor(props: React.PropsWithChildren<{}>) {
    super(props)
    this.state = { hasError: false }
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Database query error:', error, errorInfo)
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50">
          <div className="max-w-md w-full bg-white shadow-lg rounded-lg p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-2">
              Something went wrong
            </h2>
            <p className="text-gray-600 mb-4">
              Unable to load data. Please try refreshing the page.
            </p>
            <button
              onClick={() => window.location.reload()}
              className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700"
            >
              Refresh Page
            </button>
          </div>
        </div>
      )
    }
    return this.props.children
  }
}
```

### Phase 8: Real-time Updates (Optional Enhancement)

Create `UI/src/hooks/useRealtimeArticles.ts`:
```typescript
import { useEffect, useState } from 'react'
import { supabase } from '@/lib/supabase'
import { Article } from '@/types'
import { transformArticleRow } from '@/lib/transformers'

export function useRealtimeArticles() {
  const [latestArticles, setLatestArticles] = useState<Article[]>([])

  useEffect(() => {
    const channel = supabase
      .channel('articles')
      .on(
        'postgres_changes',
        {
          event: 'INSERT',
          schema: 'public',
          table: 'articles',
          filter: 'is_duplicate=eq.false'
        },
        (payload) => {
          const newArticle = transformArticleRow(payload.new as any)
          setLatestArticles(prev => [newArticle, ...prev].slice(0, 10))
        }
      )
      .subscribe()

    return () => {
      supabase.removeChannel(channel)
    }
  }, [])

  return latestArticles
}
```

### Phase 9: Deployment Configuration

#### 9.1 Update Vercel Environment Variables
```bash
cd UI
npx vercel env add NEXT_PUBLIC_SUPABASE_URL production
npx vercel env add NEXT_PUBLIC_SUPABASE_ANON_KEY production
```

#### 9.2 Update Next.js Configuration
Update `UI/next.config.ts`:
```typescript
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  images: {
    remotePatterns: [
      { protocol: "https", hostname: "static.arxiv.org" },
      { protocol: "https", hostname: "cdn.arstechnica.net" },
      { protocol: "https", hostname: "raw.githubusercontent.com" },
      { protocol: "https", hostname: "user-images.githubusercontent.com" },
      { protocol: "https", hostname: "i.ytimg.com" },
    ],
  },
  output: 'standalone',
  experimental: {
    ppr: true, // Partial Pre-Rendering for better performance
  },
};

export default nextConfig;
```

### Phase 10: Cleanup Old Code

Remove old API implementation:
```bash
rm UI/src/lib/api.ts
```

Update all component imports to use new Supabase queries instead of old API client.

## Validation Gates

### 1. Type Checking
```bash
cd UI
npx tsc --noEmit
```

### 2. Lint Check
```bash
npm run lint
```

### 3. RLS Policy Verification
Use Supabase MCP:
```sql
-- Test anonymous read access
SET ROLE anon;
SELECT COUNT(*) FROM articles LIMIT 1;
SELECT COUNT(*) FROM daily_digests LIMIT 1;

-- Test write protection
INSERT INTO articles (title, content, url, source, source_id, published_at)
VALUES ('test', 'test', 'test', 'arxiv', 'test', NOW());
-- Should fail

RESET ROLE;
```

### 4. Performance Check
```sql
EXPLAIN ANALYZE 
SELECT * FROM articles 
WHERE source = 'arxiv' 
ORDER BY published_at DESC 
LIMIT 20;
-- Should use indexes, execution time < 50ms
```

### 5. Build Verification
```bash
cd UI
npm run build
```

### 6. Local Testing
```bash
npm run dev
# Test all pages load correctly
# Verify data appears
# Check filtering works
# Test search functionality
```

## Migration Checklist

### Pre-Migration
- [ ] Backup current frontend code
- [ ] Get Supabase project URL and anon key
- [ ] Verify database schema matches specification
- [ ] Add missing enum values if needed

### Implementation
- [ ] Install Supabase client dependencies
- [ ] Create Supabase client configuration
- [ ] Set up environment variables
- [ ] Enable RLS on all tables
- [ ] Create read-only policies
- [ ] Generate TypeScript types
- [ ] Implement query service
- [ ] Update React hooks
- [ ] Create database indexes
- [ ] Update error handling components

### Testing
- [ ] Type checking passes
- [ ] Lint checks pass
- [ ] RLS policies work correctly
- [ ] Performance benchmarks met (< 50ms queries)
- [ ] Build succeeds
- [ ] All pages load without errors
- [ ] Articles display with filtering
- [ ] Search functionality works
- [ ] Digests page loads content
- [ ] Stats display correctly

### Deployment
- [ ] Set Vercel environment variables
- [ ] Deploy to staging
- [ ] Test staging deployment
- [ ] Deploy to production
- [ ] Monitor for errors

## Rollback Strategy

If issues occur:
1. Revert Git commits to restore old API client
2. Keep RLS policies (they don't affect other systems)
3. Restore environment variables if changed
4. Redeploy previous version

## MCP Tool Usage Summary

### Context7 MCP
- Library documentation retrieval
- Code examples for Supabase/Next.js integration
- Best practices and patterns

### Supabase MCP
- Schema inspection and validation
- RLS policy creation and testing
- Database migrations and index creation
- Type generation
- Performance analysis

### IDE MCP (if available)
- TypeScript validation
- Build verification
- Diagnostics

## Success Metrics

### Technical
- **Query Performance**: < 50ms for list queries
- **Type Safety**: 100% TypeScript coverage
- **Error Rate**: < 1% of requests
- **Bundle Size**: No significant increase

### Business
- **Zero Infrastructure Cost**: No API server needed
- **Improved Performance**: 2-3x faster data loading
- **Developer Experience**: Type-safe queries with auto-completion
- **Scalability**: Handles 10k+ concurrent users via Supabase

## Troubleshooting Guide

### Common Issues

#### 1. RLS Policy Errors
```sql
-- Debug policies
SELECT * FROM pg_policies WHERE tablename = 'articles';

-- Test as anonymous
SET ROLE anon;
SELECT current_user;
SELECT COUNT(*) FROM articles;
RESET ROLE;
```

#### 2. Type Mismatches
```bash
# Regenerate types
npx supabase gen types typescript --project-id YOUR_PROJECT_ID > src/types/database.ts
```

#### 3. Performance Issues
```sql
-- Check query plan
EXPLAIN ANALYZE <your_query>;

-- Verify indexes exist
SELECT * FROM pg_indexes WHERE schemaname = 'public';
```

#### 4. Environment Variables Not Loading
```bash
# Verify .env.local exists
cat UI/.env.local

# Check Vercel environment
npx vercel env ls
```

## Additional Resources

### Documentation Links
- [Supabase JS Client Docs](https://supabase.com/docs/reference/javascript/introduction)
- [Next.js with Supabase Guide](https://supabase.com/docs/guides/getting-started/quickstarts/nextjs)
- [RLS Best Practices](https://supabase.com/docs/guides/database/postgres/row-level-security)
- [SWR Documentation](https://swr.vercel.app/docs/getting-started)

### Support Channels
- Supabase Discord: https://discord.supabase.com
- GitHub Issues: Report implementation issues
- Stack Overflow: Tag with `supabase` and `nextjs`

## Final Implementation Notes

This PRP provides a complete migration path from API-dependent to direct Supabase access. The implementation:

1. **Preserves existing functionality** - All current features remain intact
2. **Improves performance** - Direct database access eliminates API latency
3. **Enhances security** - RLS policies provide fine-grained access control
4. **Reduces complexity** - Removes entire API layer
5. **Enables new features** - Real-time updates, vector similarity search

The migration is designed for single-pass implementation with comprehensive testing gates to ensure success.

---

**Confidence Score: 9/10**

The only uncertainty is around potential database-specific configurations that might exist but aren't documented. The implementation path is clear and well-tested in production environments.