# Frontend Direct Supabase Access Specification

## Overview

This specification details the migration from API-dependent frontend architecture to a modern JAMstack pattern with direct Supabase database access. This approach eliminates the need for a backend API server while maintaining security through Row Level Security (RLS) policies.

## Current vs Target Architecture

### Current (Problematic) Architecture
```
Frontend (Vercel) → API Server (Missing) → Supabase Database
GitHub Actions → Process Data → Supabase Database
```

### Target (Modern JAMstack) Architecture
```
Frontend (Vercel) → Supabase Client → Supabase Database (with RLS)
GitHub Actions → Process Data → Supabase Database
```

## Benefits of Direct Supabase Access

### Technical Benefits
- **Zero Infrastructure**: No API server to deploy or maintain
- **Sub-50ms Response Times**: Direct connection via Supabase global CDN
- **Auto-scaling**: Built-in connection pooling and load balancing
- **Real-time Capabilities**: Supabase subscriptions for live updates
- **Type Safety**: Auto-generated TypeScript types from database schema

### Business Benefits
- **Cost Optimization**: Eliminates API server hosting costs
- **Simplified Deployment**: Single frontend deployment
- **Portfolio Showcase**: Demonstrates modern JAMstack architecture
- **Industry Standard**: Used by Vercel, Netlify, and modern SaaS products

## Database Schema Reference

> **⚠️ Important**: Before implementing this specification, update the database schema to include missing article source types. Run this migration in Supabase SQL Editor:
> 
> ```sql
> -- Add missing source types to existing enum
> ALTER TYPE article_source ADD VALUE 'youtube';
> ALTER TYPE article_source ADD VALUE 'huggingface'; 
> ALTER TYPE article_source ADD VALUE 'reddit';
> ALTER TYPE article_source ADD VALUE 'github';
> ```

### Articles Table
```sql
CREATE TABLE articles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id TEXT NOT NULL,
    source article_source NOT NULL, -- enum: 'arxiv', 'hackernews', 'rss', 'youtube', 'huggingface', 'reddit', 'github'
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
    embedding vector(384), -- Native pgvector type for similarity search
    -- ⚠️ Note: SQLAlchemy model in src/models/database.py still uses Text type
    -- This discrepancy needs resolution for vector operations
    is_duplicate BOOLEAN DEFAULT FALSE,
    duplicate_of UUID REFERENCES articles(id),
    UNIQUE(source, source_id)
);
```

### Daily Digests Table
```sql
CREATE TABLE daily_digests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    digest_date DATE NOT NULL UNIQUE,
    summary_text TEXT NOT NULL,
    total_articles_processed INTEGER NOT NULL,
    audio_url TEXT,
    audio_duration INTEGER, -- Duration in seconds
    audio_size INTEGER, -- File size in bytes
    voice_type VARCHAR(50) DEFAULT 'news', -- Voice type used for TTS
    audio_generated_at TIMESTAMP WITH TIME ZONE, -- When audio was generated
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
    -- ⚠️ Note: SQLAlchemy model in src/models/database.py is missing the audio fields
    -- Only includes: audio_url but not audio_duration, audio_size, voice_type, audio_generated_at
);
```

### Digest Articles Junction Table
```sql
CREATE TABLE digest_articles (
    digest_id UUID REFERENCES daily_digests(id),
    article_id UUID REFERENCES articles(id),
    PRIMARY KEY (digest_id, article_id)
);
```

## Implementation Plan

### Phase 1: Setup Supabase Client

#### 1.1 Install Dependencies
```bash
cd UI
npm install @supabase/supabase-js
npm install @supabase/auth-ui-react  # Optional for future auth
npm install @types/node --save-dev    # For environment variables

# Update package.json to include required dependencies
npm install --save @supabase/supabase-js@^2.39.0
```

#### 1.2 Create Supabase Client
Create `UI/src/lib/supabase.ts`:
```typescript
import { createClient } from '@supabase/supabase-js'
import { Database } from '@/types/database'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!

export const supabase = createClient<Database>(supabaseUrl, supabaseAnonKey, {
  auth: {
    persistSession: false, // Since we're using anonymous access
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

// Export type for components
export type SupabaseClient = typeof supabase
```

#### 1.3 Environment Variables
Add to `UI/.env.local`:
```env
NEXT_PUBLIC_SUPABASE_URL=your_supabase_project_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
```

Update Vercel environment variables:
```bash
cd UI
npx vercel env add NEXT_PUBLIC_SUPABASE_URL production
npx vercel env add NEXT_PUBLIC_SUPABASE_ANON_KEY production
```

### Phase 2: Row Level Security (RLS) Setup

#### 2.1 Enable RLS on Tables
```sql
-- Enable RLS on all tables
ALTER TABLE articles ENABLE ROW LEVEL SECURITY;
ALTER TABLE daily_digests ENABLE ROW LEVEL SECURITY;
ALTER TABLE digest_articles ENABLE ROW LEVEL SECURITY;
```

#### 2.2 Create Read-Only Policies
```sql
-- Allow anonymous read access to articles (unique policy name)
CREATE POLICY "Frontend anonymous read access articles" ON articles
FOR SELECT USING (true);

-- Allow anonymous read access to digests (unique policy name)
CREATE POLICY "Frontend anonymous read access digests" ON daily_digests
FOR SELECT USING (true);

-- Allow anonymous read access to digest_articles (unique policy name)
CREATE POLICY "Frontend anonymous read access digest_articles" ON digest_articles
FOR SELECT USING (true);
```

#### 2.3 Verify RLS Policies
```sql
-- Test anonymous access (should work)
SELECT COUNT(*) FROM articles;
SELECT COUNT(*) FROM daily_digests;

-- Test write access (should fail)
INSERT INTO articles (title, content, url, source, source_id, published_at)
VALUES ('test', 'test', 'test', 'arxiv', 'test', NOW());
```

### Phase 3: Database Query Implementation

#### 3.1 Create Database Types
Generate TypeScript types from Supabase schema:
```bash
cd UI
# Modern Supabase CLI command
npx supabase gen types typescript --project-id your_project_id --schema public > src/types/database.ts
# Alternative using Supabase client
npx supabase gen types typescript --linked --schema public > src/types/database.ts
```

Or create manually in `UI/src/types/database.ts`:
```typescript
export interface Database {
  public: {
    Tables: {
      articles: {
        Row: {
          id: string
          source_id: string
          source: 'arxiv' | 'hackernews' | 'rss' | 'reddit' | 'github' | 'youtube' | 'huggingface'
          title: string
          content: string
          url: string
          author: string | null
          published_at: string
          fetched_at: string
          summary: string | null
          relevance_score: number | null
          categories: string[]
          key_points: string[]
          embedding: number[] | null  // Vector embedding array
          is_duplicate: boolean
          duplicate_of: string | null
        }
        Insert: {
          id?: string
          source_id: string
          source: 'arxiv' | 'hackernews' | 'rss' | 'reddit' | 'github' | 'youtube' | 'huggingface'
          title: string
          content: string
          url: string
          author?: string | null
          published_at: string
          fetched_at?: string
          summary?: string | null
          relevance_score?: number | null
          categories?: string[]
          key_points?: string[]
          embedding?: number[] | null  // Vector embedding array
          is_duplicate?: boolean
          duplicate_of?: string | null
        }
        Update: {
          id?: string
          source_id?: string
          source?: 'arxiv' | 'hackernews' | 'rss' | 'reddit' | 'github' | 'youtube' | 'huggingface'
          title?: string
          content?: string
          url?: string
          author?: string | null
          published_at?: string
          fetched_at?: string
          summary?: string | null
          relevance_score?: number | null
          categories?: string[]
          key_points?: string[]
          embedding?: number[] | null  // Vector embedding array
          is_duplicate?: boolean
          duplicate_of?: string | null
        }
      }
      daily_digests: {
        Row: {
          id: string
          digest_date: string
          summary_text: string
          total_articles_processed: number
          audio_url: string | null
          audio_duration: number | null
          audio_size: number | null
          voice_type: string | null
          audio_generated_at: string | null
          created_at: string
        }
        Insert: {
          id?: string
          digest_date: string
          summary_text: string
          total_articles_processed: number
          audio_url?: string | null
          audio_duration?: number | null
          audio_size?: number | null
          voice_type?: string | null
          audio_generated_at?: string | null
          created_at?: string
        }
        Update: {
          id?: string
          digest_date?: string
          summary_text?: string
          total_articles_processed?: number
          audio_url?: string | null
          audio_duration?: number | null
          audio_size?: number | null
          voice_type?: string | null
          audio_generated_at?: string | null
          created_at?: string
        }
      }
      digest_articles: {
        Row: {
          digest_id: string
          article_id: string
        }
        Insert: {
          digest_id: string
          article_id: string
        }
        Update: {
          digest_id?: string
          article_id?: string
        }
      }
    }
  }
}
```

#### 3.2 Create Supabase Query Service
Create `UI/src/lib/supabase-queries.ts`:
```typescript
import { supabase } from './supabase'
import { Database } from '@/types/database'
import { Article, ArticleFilters, Digest, Stats, PaginationMeta } from '@/types'

type ArticleRow = Database['public']['Tables']['articles']['Row']
type DigestRow = Database['public']['Tables']['daily_digests']['Row']

// Transform database row to frontend Article type
function transformArticleRow(row: ArticleRow): Article {
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

// Transform database row to frontend Digest type
function transformDigestRow(row: DigestRow, articles: Article[] = []): Digest {
  return {
    id: row.id,
    title: `Daily Digest - ${new Date(row.digest_date).toLocaleDateString()}`,
    summary: row.summary_text,
    key_points: [], // Could be extracted from summary_text
    audio_url: row.audio_url || '',
    duration: row.audio_duration || 0,
    articles,
    created_at: row.created_at,
  }
}

export const supabaseQueries = {
  // Articles
  async getArticles(filters: ArticleFilters & { page?: number; per_page?: number } = {}) {
    const {
      source,
      category,
      relevance_min,
      time_range,
      page = 1,
      per_page = 20
    } = filters

    let query = supabase
      .from('articles')
      .select('*', { count: 'exact' })
      .eq('is_duplicate', false)
      .order('published_at', { ascending: false })

    // Apply filters
    if (source) {
      query = query.eq('source', source)
    }

    if (category) {
      query = query.contains('categories', [category])
    }

    if (relevance_min !== undefined) {
      query = query.gte('relevance_score', relevance_min)
    }

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

    // Apply pagination
    const from = (page - 1) * per_page
    const to = from + per_page - 1
    query = query.range(from, to)

    const { data, error, count } = await query

    if (error) {
      throw new Error(`Failed to fetch articles: ${error.message}`)
    }

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

  async getArticle(id: string): Promise<Article> {
    const { data, error } = await supabase
      .from('articles')
      .select('*')
      .eq('id', id)
      .single()

    if (error) {
      throw new Error(`Failed to fetch article: ${error.message}`)
    }

    if (!data) {
      throw new Error('Article not found')
    }

    return transformArticleRow(data)
  },

  async searchArticles(query: string, options: { limit?: number; offset?: number } = {}) {
    const { limit = 20, offset = 0 } = options

    // Use PostgreSQL full-text search with existing search function
    const { data, error, count } = await supabase
      .rpc('search_articles_fulltext', {
        query_text: query,
        max_results: limit,
        skip_results: offset
      })

    if (error) {
      // Fallback to basic text search if function doesn't exist
      console.warn('Using fallback search:', error.message)
      const fallback = await supabase
        .from('articles')
        .select('*', { count: 'exact' })
        .or(`title.ilike.%${query}%,content.ilike.%${query}%,summary.ilike.%${query}%`)
        .eq('is_duplicate', false)
        .order('relevance_score', { ascending: false, nullsLast: true })
        .order('published_at', { ascending: false })
        .range(offset, offset + limit - 1)

      if (fallback.error) {
        throw new Error(`Search failed: ${fallback.error.message}`)
      }

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

  // Vector similarity search for related articles
  async getSimilarArticles(articleId: string, options: { limit?: number; threshold?: number } = {}) {
    const { limit = 5, threshold = 0.85 } = options

    // First get the embedding of the target article
    const { data: article, error: articleError } = await supabase
      .from('articles')
      .select('embedding')
      .eq('id', articleId)
      .single()

    if (articleError || !article?.embedding) {
      throw new Error('Article not found or has no embedding')
    }

    // Use the match_articles function for similarity search
    const { data, error } = await supabase
      .rpc('match_articles', {
        query_embedding: article.embedding,
        match_threshold: threshold,
        match_count: limit
      })

    if (error) {
      throw new Error(`Similarity search failed: ${error.message}`)
    }

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

  // Digests
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

    if (error && error.code !== 'PGRST116') { // PGRST116 = no rows returned
      throw new Error(`Failed to fetch latest digest: ${error.message}`)
    }

    if (!data) {
      return null
    }

    // Extract articles from the join
    const articles = (data.digest_articles as any[])
      ?.map((da: any) => da.articles)
      ?.filter(Boolean)
      ?.map(transformArticleRow) || []

    return transformDigestRow(data, articles)
  },

  async getDigest(id: string): Promise<Digest> {
    const { data, error } = await supabase
      .from('daily_digests')
      .select(`
        *,
        digest_articles!inner(
          articles(*)
        )
      `)
      .eq('id', id)
      .single()

    if (error) {
      throw new Error(`Failed to fetch digest: ${error.message}`)
    }

    if (!data) {
      throw new Error('Digest not found')
    }

    // Extract articles from the join
    const articles = (data.digest_articles as any[])
      ?.map((da: any) => da.articles)
      ?.filter(Boolean)
      ?.map(transformArticleRow) || []

    return transformDigestRow(data, articles)
  },

  async getDigests(options: { page?: number; per_page?: number } = {}) {
    const { page = 1, per_page = 10 } = options

    const from = (page - 1) * per_page
    const to = from + per_page - 1

    const { data, error, count } = await supabase
      .from('daily_digests')
      .select('*', { count: 'exact' })
      .order('digest_date', { ascending: false })
      .range(from, to)

    if (error) {
      throw new Error(`Failed to fetch digests: ${error.message}`)
    }

    const digests = data?.map(row => transformDigestRow(row)) || []
    const total = count || 0
    const total_pages = Math.ceil(total / per_page)

    return {
      digests,
      pagination: {
        page,
        per_page,
        total,
        total_pages,
        has_next: page < total_pages,
        has_prev: page > 1,
      } as PaginationMeta
    }
  },

  // Statistics
  async getStats(): Promise<Stats> {
    // Get total articles
    const { count: totalArticles, error: totalError } = await supabase
      .from('articles')
      .select('*', { count: 'exact', head: true })
      .eq('is_duplicate', false)

    if (totalError) {
      throw new Error(`Failed to get total articles: ${totalError.message}`)
    }

    // Get articles by source
    const { data: sourceData, error: sourceError } = await supabase
      .from('articles')
      .select('source')
      .eq('is_duplicate', false)

    if (sourceError) {
      throw new Error(`Failed to get articles by source: ${sourceError.message}`)
    }

    // Get articles by category
    const { data: categoryData, error: categoryError } = await supabase
      .from('articles')
      .select('categories')
      .eq('is_duplicate', false)
      .not('categories', 'is', null)

    if (categoryError) {
      throw new Error(`Failed to get articles by category: ${categoryError.message}`)
    }

    // Get average relevance score
    const { data: avgData, error: avgError } = await supabase
      .rpc('get_avg_relevance_score')

    if (avgError) {
      console.warn('Failed to get average relevance score:', avgError.message)
    }

    // Get articles from last 24h
    const oneDayAgo = new Date(Date.now() - 24 * 60 * 60 * 1000)
    const { count: last24h, error: last24hError } = await supabase
      .from('articles')
      .select('*', { count: 'exact', head: true })
      .eq('is_duplicate', false)
      .gte('published_at', oneDayAgo.toISOString())

    if (last24hError) {
      console.warn('Failed to get last 24h articles:', last24hError.message)
    }

    // Get articles from last week
    const oneWeekAgo = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000)
    const { count: lastWeek, error: lastWeekError } = await supabase
      .from('articles')
      .select('*', { count: 'exact', head: true })
      .eq('is_duplicate', false)
      .gte('published_at', oneWeekAgo.toISOString())

    if (lastWeekError) {
      console.warn('Failed to get last week articles:', lastWeekError.message)
    }

    // Aggregate statistics
    const articles_by_source: Record<string, number> = {}
    sourceData?.forEach(item => {
      articles_by_source[item.source] = (articles_by_source[item.source] || 0) + 1
    })

    const articles_by_category: Record<string, number> = {}
    categoryData?.forEach(item => {
      item.categories?.forEach(category => {
        articles_by_category[category] = (articles_by_category[category] || 0) + 1
      })
    })

    return {
      total_articles: totalArticles || 0,
      articles_by_source,
      articles_by_category,
      avg_relevance_score: avgData?.[0]?.avg_relevance || 0,
      articles_last_24h: last24h || 0,
      articles_last_week: lastWeek || 0,
    }
  }
}

// Helper function to create database function for average relevance score
export const createHelperFunctions = `
-- Create function to get average relevance score
CREATE OR REPLACE FUNCTION get_avg_relevance_score()
RETURNS TABLE(avg_relevance REAL) AS $$
BEGIN
  RETURN QUERY
  SELECT AVG(relevance_score)::REAL as avg_relevance
  FROM articles
  WHERE is_duplicate = false AND relevance_score IS NOT NULL;
END;
$$ LANGUAGE plpgsql;
`
```

### Phase 4: Update React Hooks

#### 4.1 Replace useArticles Hook
Update `UI/src/hooks/useArticles.ts`:
```typescript
import useSWR from 'swr'
import { supabaseQueries } from '@/lib/supabase-queries'
import { ArticleFilters } from '@/types'

export function useArticles(source?: string, filters?: ArticleFilters) {
  const key = source
    ? ['articles', source, filters]
    : ['articles', filters]
    
  return useSWR(key, () =>
    supabaseQueries.getArticles({
      source,
      ...filters
    })
  )
}

export function useArticle(id: string) {
  return useSWR(
    id ? ['article', id] : null,
    () => supabaseQueries.getArticle(id)
  )
}

export function useDigest() {
  return useSWR('digest', supabaseQueries.getLatestDigest, {
    refreshInterval: 60000, // Refresh every minute
  })
}

export function useStats() {
  return useSWR('stats', supabaseQueries.getStats, {
    refreshInterval: 30000, // Refresh every 30 seconds
  })
}

// New hooks for enhanced functionality
export function useDigests(page = 1, per_page = 10) {
  return useSWR(
    ['digests', page, per_page],
    () => supabaseQueries.getDigests({ page, per_page })
  )
}

export function useSearch(query: string, options?: { limit?: number; offset?: number }) {
  return useSWR(
    query ? ['search', query, options] : null,
    () => supabaseQueries.searchArticles(query, options),
    {
      revalidateOnFocus: false, // Don't re-search when window gains focus
      dedupingInterval: 5000, // Cache for 5 seconds
    }
  )
}
```

#### 4.2 Create Real-time Hooks (Optional)
Create `UI/src/hooks/useRealtimeArticles.ts`:
```typescript
import { useEffect, useState } from 'react'
import { supabase } from '@/lib/supabase'
import { Article } from '@/types'

export function useRealtimeArticles() {
  const [latestArticles, setLatestArticles] = useState<Article[]>([])

  useEffect(() => {
    // Subscribe to new articles
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
          console.log('New article:', payload.new)
          // Transform and add to latest articles
          // Implementation depends on your needs
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

### Phase 5: Error Handling and Loading States

#### 5.1 Create Error Boundary
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
              Unable to load data from the database. Please try refreshing the page.
            </p>
            <button
              onClick={() => window.location.reload()}
              className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 transition-colors"
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

#### 5.2 Update Loading Components
Enhance `UI/src/components/Skeleton.tsx`:
```typescript
import React from 'react'

export function ArticleSkeleton() {
  return (
    <div className="bg-white rounded-lg shadow-md p-6 animate-pulse">
      <div className="h-6 bg-gray-300 rounded mb-4"></div>
      <div className="h-4 bg-gray-300 rounded mb-2"></div>
      <div className="h-4 bg-gray-300 rounded mb-4 w-3/4"></div>
      <div className="flex justify-between items-center">
        <div className="h-4 bg-gray-300 rounded w-20"></div>
        <div className="h-4 bg-gray-300 rounded w-24"></div>
      </div>
    </div>
  )
}

export function DigestSkeleton() {
  return (
    <div className="bg-white rounded-lg shadow-md p-6 animate-pulse">
      <div className="h-8 bg-gray-300 rounded mb-4"></div>
      <div className="h-4 bg-gray-300 rounded mb-2"></div>
      <div className="h-4 bg-gray-300 rounded mb-2"></div>
      <div className="h-4 bg-gray-300 rounded mb-4 w-2/3"></div>
      <div className="h-10 bg-gray-300 rounded"></div>
    </div>
  )
}

export function StatsSkeleton() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6 animate-pulse">
      {[...Array(6)].map((_, i) => (
        <div key={i} className="bg-white rounded-lg shadow-md p-6">
          <div className="h-4 bg-gray-300 rounded mb-2"></div>
          <div className="h-8 bg-gray-300 rounded"></div>
        </div>
      ))}
    </div>
  )
}
```

### Phase 6: Remove Old API Code

#### 6.1 Files to Delete/Update
```bash
# Delete old API implementation
rm UI/src/lib/api.ts

# Update imports across components
# Replace: import { api } from '@/lib/api'
# With: import { supabaseQueries } from '@/lib/supabase-queries'
```

#### 6.2 Update Component Imports
Update all components that used the old API:
- `UI/src/app/articles/page.tsx`
- `UI/src/app/digests/page.tsx`
- `UI/src/app/search/page.tsx`
- `UI/src/app/sources/page.tsx`

### Phase 7: Performance Optimizations

#### 7.1 Implement Query Caching
Create `UI/src/lib/query-cache.ts`:
```typescript
import { unstable_cache } from 'next/cache'
import { supabaseQueries } from './supabase-queries'

// Cache expensive queries for 5 minutes
export const getCachedStats = unstable_cache(
  () => supabaseQueries.getStats(),
  ['stats'],
  { revalidate: 300 } // 5 minutes
)

export const getCachedArticles = unstable_cache(
  (filters: any) => supabaseQueries.getArticles(filters),
  ['articles'],
  { revalidate: 60 } // 1 minute
)
```

#### 7.2 Add Database Indexes
Run these SQL commands in Supabase SQL Editor:
```sql
-- Optimize article queries
CREATE INDEX IF NOT EXISTS idx_articles_published_at_desc ON articles(published_at DESC);
CREATE INDEX IF NOT EXISTS idx_articles_source_published ON articles(source, published_at DESC);
CREATE INDEX IF NOT EXISTS idx_articles_relevance_score ON articles(relevance_score DESC) WHERE relevance_score IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_articles_categories_gin ON articles USING gin(categories);

-- Optimize text search
CREATE INDEX IF NOT EXISTS idx_articles_title_gin ON articles USING gin(to_tsvector('english', title));
CREATE INDEX IF NOT EXISTS idx_articles_content_gin ON articles USING gin(to_tsvector('english', content));

-- Optimize digest queries
CREATE INDEX IF NOT EXISTS idx_digests_date_desc ON daily_digests(digest_date DESC);
CREATE INDEX IF NOT EXISTS idx_digest_articles_digest_id ON digest_articles(digest_id);
```

### Phase 8: Testing Strategy

#### 8.1 Create Test Utilities
Create `UI/src/lib/__tests__/supabase-queries.test.ts`:
```typescript
import { supabaseQueries } from '../supabase-queries'

// Mock Supabase client
jest.mock('../supabase', () => ({
  supabase: {
    from: jest.fn(() => ({
      select: jest.fn(() => ({
        eq: jest.fn(() => ({
          order: jest.fn(() => ({
            range: jest.fn(() => ({
              then: jest.fn()
            }))
          }))
        }))
      }))
    }))
  }
}))

describe('supabaseQueries', () => {
  describe('getArticles', () => {
    it('should fetch articles with default parameters', async () => {
      // Test implementation
    })

    it('should apply filters correctly', async () => {
      // Test filtering logic
    })

    it('should handle pagination', async () => {
      // Test pagination
    })
  })

  describe('searchArticles', () => {
    it('should perform text search', async () => {
      // Test search functionality
    })
  })
})
```

#### 8.2 Integration Tests
Create `UI/src/lib/__tests__/integration.test.ts`:
```typescript
import { supabase } from '../supabase'

describe('Supabase Integration', () => {
  it('should connect to database', async () => {
    const { data, error } = await supabase
      .from('articles')
      .select('count(*)')
      .limit(1)

    expect(error).toBeNull()
    expect(data).toBeDefined()
  })

  it('should respect RLS policies', async () => {
    // Test that write operations are blocked
    const { error } = await supabase
      .from('articles')
      .insert({
        title: 'test',
        content: 'test',
        url: 'test',
        source: 'arxiv',
        source_id: 'test',
        published_at: new Date().toISOString()
      })

    expect(error).toBeTruthy()
    expect(error?.message).toContain('not allowed')
  })
})
```

### Phase 9: Deployment Configuration

#### 9.1 Update Vercel Configuration
Create `UI/vercel.json`:
```json
{
  "env": {
    "NEXT_PUBLIC_SUPABASE_URL": "@supabase-url",
    "NEXT_PUBLIC_SUPABASE_ANON_KEY": "@supabase-anon-key"
  },
  "build": {
    "env": {
      "NEXT_PUBLIC_SUPABASE_URL": "@supabase-url",
      "NEXT_PUBLIC_SUPABASE_ANON_KEY": "@supabase-anon-key"
    }
  }
}
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
  // Optimize for serverless functions
  output: 'standalone',
  experimental: {
    // Enable PPR for better performance
    ppr: true,
  },
};

export default nextConfig;
```

### Phase 10: Migration Checklist

#### Pre-Migration Checklist
- [ ] Supabase project URL and anon key available
- [ ] RLS policies created and tested
- [ ] Database indexes created
- [ ] Environment variables configured in Vercel
- [ ] Backup of current frontend code

#### Migration Steps
1. [ ] Install Supabase client dependencies
2. [ ] Create Supabase client configuration
3. [ ] Implement database query service
4. [ ] Update React hooks to use new queries
5. [ ] Update all components to use new hooks
6. [ ] Remove old API code
7. [ ] Test locally with real Supabase data
8. [ ] Deploy to Vercel staging
9. [ ] Test staging deployment
10. [ ] Deploy to production

#### Post-Migration Verification
- [ ] All pages load without errors
- [ ] Articles display correctly with filtering
- [ ] Search functionality works
- [ ] Digests page loads with content
- [ ] Stats page shows accurate data
- [ ] Real-time updates work (if implemented)
- [ ] Performance is acceptable (< 2s page load)

## Success Metrics

### Technical Metrics
- **Page Load Time**: < 2 seconds for article list
- **Database Query Time**: < 500ms for most queries
- **Error Rate**: < 1% of requests
- **Cache Hit Rate**: > 80% for repeated queries

### Business Metrics
- **Zero Infrastructure Costs**: No API server hosting fees
- **Deployment Simplicity**: Single command deployment
- **Developer Experience**: Type-safe queries with auto-completion
- **Scalability**: Handles 10k+ concurrent users via Supabase

## Troubleshooting Guide

### Common Issues

#### 1. RLS Policy Errors
```sql
-- Debug RLS policies
SELECT * FROM pg_policies WHERE tablename = 'articles';

-- Test policy as anonymous user
SET ROLE anon;
SELECT COUNT(*) FROM articles;
RESET ROLE;
```

#### 2. Type Errors
```bash
# Regenerate types from Supabase
npx supabase gen types typescript --project-id YOUR_PROJECT_ID > src/types/database.ts
```

#### 3. Performance Issues
```sql
-- Check query performance
EXPLAIN ANALYZE SELECT * FROM articles 
WHERE source = 'arxiv' 
ORDER BY published_at DESC 
LIMIT 20;
```

#### 4. Environment Variable Issues
```bash
# Verify environment variables
cd UI
npx vercel env ls
npx vercel env pull .env.local
```

### Support Resources
- **Supabase Documentation**: https://supabase.com/docs
- **Next.js with Supabase**: https://supabase.com/docs/guides/getting-started/quickstarts/nextjs
- **SWR Documentation**: https://swr.vercel.app/docs/getting-started

## Conclusion

This specification provides a comprehensive migration path from an API-dependent frontend to a modern JAMstack architecture with direct Supabase access. The resulting system will be:

- **More Performant**: Direct database access eliminates API latency
- **More Secure**: RLS policies provide fine-grained access control
- **More Cost-Effective**: Zero infrastructure costs for API layer
- **More Scalable**: Leverages Supabase's global infrastructure
- **More Maintainable**: Simpler architecture with fewer moving parts

The migration preserves all existing functionality while providing a foundation for future enhancements like real-time updates, advanced search, and user authentication.