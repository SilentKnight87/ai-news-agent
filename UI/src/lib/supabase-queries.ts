import { supabase } from './supabase'
import { Database } from '@/types/database'
import { 
  Article, 
  ArticleFilters, 
  Digest, 
  DigestSummary,
  Stats, 
  PaginationMeta, 
  SearchResponse,
  FilterResponse,
  PaginatedArticleResponse,
  SourceMetadata,
  FiltersApplied 
} from '@/types'
import { 
  transformArticleRow,
  transformArticleProjectedRow,
  transformDigestRow, 
  transformDigestToSummary,
  transformSourceMetadata,
  transformStats,
  transformDatabaseError 
} from './transformers'

/**
 * Comprehensive Supabase query service for AI News Aggregator.
 * Provides type-safe database access with filtering, pagination, and search.
 */
export const supabaseQueries = {
  /**
   * Get articles with advanced filtering and pagination.
   * Supports source filtering, category filtering, relevance scoring, and time ranges.
   * 
   * Args:
   *   filters: Combined filter and pagination parameters
   * 
   * Returns:
   *   PaginatedArticleResponse: Articles with pagination metadata
   */
  async getArticles(
    filters: ArticleFilters & { 
      page?: number
      per_page?: number
      sort_by?: 'published_at' | 'relevance_score' | 'title' | 'fetched_at'
      order?: 'asc' | 'desc'
    } = {}
  ): Promise<PaginatedArticleResponse> {
    const { 
      category, 
      relevance_min, 
      time_range, 
      page = 1, 
      per_page = 20,
      sort_by = 'published_at',
      order = 'desc'
    } = filters

    let query = supabase
      .from('articles')
      .select('id, title, url, source, summary, relevance_score, categories, published_at, fetched_at', { count: 'exact' })
      .eq('is_duplicate', false)

    // Apply filters
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

    // Apply sorting
    const ascending = order === 'asc'
    query = query.order(sort_by, { ascending, nullsFirst: false })

    // Apply pagination
    const from = (page - 1) * per_page
    const to = from + per_page - 1
    query = query.range(from, to)

    try {
      const { data, error, count } = await query

      if (error) {
        throw new Error(`Failed to fetch articles: ${transformDatabaseError(error)}`)
      }

      const articles = data?.map(transformArticleProjectedRow) || []
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
        },
        meta: {
          sort_by,
          order,
          cache_hit: false,
        },
      }
    } catch (error: unknown) {
      throw new Error(`Articles query failed: ${transformDatabaseError(error)}`)
    }
  },

  /**
   * Get articles from a specific source with pagination.
   * Optimized for source-specific browsing.
   */
  async getArticlesBySource(
    source: string,
    options: { 
      page?: number
      per_page?: number
      relevance_min?: number
    } = {}
  ): Promise<PaginatedArticleResponse> {
    const { page = 1, per_page = 20, relevance_min } = options

    let query = supabase
      .from('articles')
      .select('id, title, url, source, summary, relevance_score, categories, published_at, fetched_at', { count: 'exact' })
      .eq('source', source as Database['public']['Enums']['article_source'])
      .eq('is_duplicate', false)
      .order('published_at', { ascending: false })

    if (relevance_min !== undefined) {
      query = query.gte('relevance_score', relevance_min)
    }

    const from = (page - 1) * per_page
    const to = from + per_page - 1
    query = query.range(from, to)

    try {
      const { data, error, count } = await query

      if (error) {
        throw new Error(`Failed to fetch ${source} articles: ${transformDatabaseError(error)}`)
      }

      const articles = data?.map(transformArticleProjectedRow) || []
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
        },
        meta: {
          sort_by: 'published_at',
          order: 'desc',
          cache_hit: false,
        },
      }
    } catch (error: unknown) {
      throw new Error(`Source articles query failed: ${transformDatabaseError(error)}`)
    }
  },

  /**
   * Get a single article by ID.
   */
  async getArticle(id: string): Promise<Article> {
    try {
      const { data, error } = await supabase
        .from('articles')
        .select('*')
        .eq('id', id)
        .single()

      if (error) {
        throw new Error(`Failed to fetch article: ${transformDatabaseError(error)}`)
      }
      
      if (!data) {
        throw new Error('Article not found')
      }

      return transformArticleRow(data)
    } catch (error: unknown) {
      throw new Error(`Article query failed: ${transformDatabaseError(error)}`)
    }
  },

  /**
   * Search articles with full-text search and ILIKE fallback.
   * Uses RPC-first approach: search_articles_fulltext() then falls back to ILIKE.
   */
  async searchArticles(
    query: string, 
    options: { 
      limit?: number
      offset?: number
      source?: string
      relevance_min?: number
    } = {}
  ): Promise<SearchResponse> {
    const { limit = 20, offset = 0, source, relevance_min } = options

    if (!query.trim()) {
      return {
        articles: [],
        total: 0,
        query,
        took_ms: 0,
      }
    }

    const startTime = Date.now()

    try {
      // TODO: Re-enable RPC search after TypeScript issues resolved
      // Fallback directly to ILIKE search for now
      console.log('Using ILIKE search directly')

      // Fallback to ILIKE-based search
      console.time('search_ilike')
      
      let searchQuery = supabase
        .from('articles')
        .select('id, title, url, source, summary, relevance_score, categories, published_at, fetched_at', { count: 'exact' })
        .or(`title.ilike.%${query}%,content.ilike.%${query}%,summary.ilike.%${query}%`)
        .eq('is_duplicate', false)

      // Apply additional filters
      if (source) {
        searchQuery = searchQuery.eq('source', source as Database['public']['Enums']['article_source'])
      }
      
      if (relevance_min !== undefined) {
        searchQuery = searchQuery.gte('relevance_score', relevance_min)
      }

      // Order by relevance score, then by published date
      searchQuery = searchQuery
        .order('relevance_score', { ascending: false, nullsFirst: false })
        .order('published_at', { ascending: false })
        .range(offset, offset + limit - 1)

      const { data, error, count } = await searchQuery

      console.timeEnd('search_ilike')

      if (error) {
        throw new Error(`Search failed: ${transformDatabaseError(error)}`)
      }

      const took_ms = Date.now() - startTime
      console.log('ILIKE search completed:', { query, total: count, took_ms })

      return {
        articles: data?.map(transformArticleProjectedRow) || [],
        total: count || 0,
        query,
        took_ms,
      }
    } catch (error: unknown) {
      throw new Error(`Search query failed: ${transformDatabaseError(error)}`)
    }
  },

  /**
   * Advanced filtering with multiple criteria.
   * Supports date ranges, relevance ranges, multiple sources, and categories.
   */
  async filterArticles(filters: {
    start_date?: string
    end_date?: string
    relevance_min?: number
    relevance_max?: number
    sources?: string[]
    categories?: string[]
    limit?: number
    offset?: number
  } = {}): Promise<FilterResponse> {
    const {
      start_date,
      end_date,
      relevance_min,
      relevance_max,
      sources,
      categories,
      limit = 20,
      offset = 0
    } = filters

    const startTime = Date.now()

    try {
      let query = supabase
        .from('articles')
        .select('id, title, url, source, summary, relevance_score, categories, published_at, fetched_at', { count: 'exact' })
        .eq('is_duplicate', false)

      // Date filters
      if (start_date) {
        query = query.gte('published_at', start_date)
      }
      if (end_date) {
        query = query.lte('published_at', end_date)
      }

      // Relevance filters
      if (relevance_min !== undefined) {
        query = query.gte('relevance_score', relevance_min)
      }
      if (relevance_max !== undefined) {
        query = query.lte('relevance_score', relevance_max)
      }

      // Source filters
      if (sources && sources.length > 0) {
        query = query.in('source', sources as Database['public']['Enums']['article_source'][])
      }

      // Category filters (array overlaps with specified categories)
      if (categories && categories.length > 0) {
        query = query.overlaps('categories', categories)
      }

      // Apply pagination and ordering
      query = query
        .order('relevance_score', { ascending: false, nullsFirst: false })
        .order('published_at', { ascending: false })
        .range(offset, offset + limit - 1)

      const { data, error, count } = await query

      if (error) {
        throw new Error(`Filter failed: ${transformDatabaseError(error)}`)
      }

      const took_ms = Date.now() - startTime

      // Build applied filters object
      const filters_applied: FiltersApplied = {}
      if (start_date) filters_applied.start_date = start_date
      if (end_date) filters_applied.end_date = end_date
      if (relevance_min !== undefined) filters_applied.relevance_min = relevance_min
      if (relevance_max !== undefined) filters_applied.relevance_max = relevance_max
      if (sources) filters_applied.sources = sources
      if (categories) filters_applied.categories = categories

      return {
        articles: data?.map(transformArticleProjectedRow) || [],
        filters_applied,
        total: count || 0,
        took_ms,
      }
    } catch (error: unknown) {
      throw new Error(`Filter query failed: ${transformDatabaseError(error)}`)
    }
  },

  /**
   * Get similar articles using pgvector similarity search.
   * Requires articles to have embeddings.
   */
  async getSimilarArticles(
    articleId: string, 
    options: { 
      limit?: number
      threshold?: number 
    } = {}
  ): Promise<{
    articles: Partial<Article>[]
    query_article_id: string
    threshold: number
  }> {
    const { limit = 5, threshold = 0.85 } = options

    try {
      // Get target article embedding
      const { data: article, error: articleError } = await supabase
        .from('articles')
        .select('embedding')
        .eq('id', articleId)
        .single()

      if (articleError || !article?.embedding) {
        throw new Error('Article not found or has no embedding')
      }

      // Use vector similarity search function
      const { data, error } = await supabase
        .rpc('match_articles', {
          query_embedding: article.embedding,
          match_threshold: threshold,
          match_count: limit
        })

      if (error) {
        throw new Error(`Similarity search failed: ${transformDatabaseError(error)}`)
      }

      return {
        articles: data?.map((item: Record<string, unknown>) => ({
          id: item.id as string,
          title: item.title as string,
          url: item.url as string,
          similarity: item.similarity as number,
          published_at: item.published_at as string,
          source: (item.source as string) || 'unknown'
        })) || [],
        query_article_id: articleId,
        threshold,
      }
    } catch (error: unknown) {
      // If vector search fails, fall back to category-based similarity
      console.warn('Vector similarity search failed, using category fallback:', error instanceof Error ? error.message : 'Unknown error')
      
      const { data: sourceArticle } = await supabase
        .from('articles')
        .select('categories, source')
        .eq('id', articleId)
        .single()

      if (!sourceArticle?.categories?.length) {
        return {
          articles: [],
          query_article_id: articleId,
          threshold,
        }
      }

      // Find articles with overlapping categories
      const { data } = await supabase
        .from('articles')
        .select('id, title, url, published_at, source, categories')
        .neq('id', articleId)
        .eq('is_duplicate', false)
        .overlaps('categories', sourceArticle.categories)
        .order('relevance_score', { ascending: false, nullsFirst: false })
        .limit(limit)

      return {
        articles: data?.map(item => ({
          id: item.id,
          title: item.title,
          url: item.url,
          published_at: item.published_at,
          source: item.source,
          similarity: 0.5 // Approximate similarity for category-based matching
        })) || [],
        query_article_id: articleId,
        threshold,
      }
    }
  },

  /**
   * Get latest daily digest with articles.
   */
  async getLatestDigest(): Promise<Digest | null> {
    try {
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
        throw new Error(`Failed to fetch latest digest: ${transformDatabaseError(error)}`)
      }

      if (!data) return null

      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const articles = ((data.digest_articles as any) || [])
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        .map((da: any) => da.articles)
        .filter(Boolean)
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        .map((articleData: any) => transformArticleRow(articleData))

      return transformDigestRow(data, articles)
    } catch (error: unknown) {
      throw new Error(`Latest digest query failed: ${transformDatabaseError(error)}`)
    }
  },

  /**
   * Get digest by ID with full article details.
   */
  async getDigestById(id: string): Promise<Digest | null> {
    try {
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

      if (error && error.code !== 'PGRST116') {
        throw new Error(`Failed to fetch digest: ${transformDatabaseError(error)}`)
      }

      if (!data) return null

      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const articles = ((data.digest_articles as any) || [])
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        .map((da: any) => da.articles)
        .filter(Boolean)
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        .map((articleData: any) => transformArticleRow(articleData))

      return transformDigestRow(data, articles)
    } catch (error: unknown) {
      throw new Error(`Digest by ID query failed: ${transformDatabaseError(error)}`)
    }
  },

  /**
   * Get paginated list of digest summaries.
   * Lightweight for digest listing pages.
   */
  async getDigestSummaries(options: {
    page?: number
    per_page?: number
  } = {}): Promise<{
    digests: DigestSummary[]
    pagination: PaginationMeta
  }> {
    const { page = 1, per_page = 10 } = options

    try {
      const from = (page - 1) * per_page
      const to = from + per_page - 1

      const { data, error, count } = await supabase
        .from('daily_digests')
        .select('*', { count: 'exact' })
        .order('digest_date', { ascending: false })
        .range(from, to)

      if (error) {
        throw new Error(`Failed to fetch digest summaries: ${transformDatabaseError(error)}`)
      }

      const digests = data?.map(transformDigestToSummary) || []
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
        },
      }
    } catch (error: unknown) {
      throw new Error(`Digest summaries query failed: ${transformDatabaseError(error)}`)
    }
  },

  /**
   * Get comprehensive statistics for dashboard.
   */
  async getStats(): Promise<Stats> {
    try {
      // Execute queries in parallel for performance
      const [
        totalResult,
        sourceResult,
        categoryResult,
        last24hResult,
        lastWeekResult,
      ] = await Promise.all([
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

      // Calculate average relevance score using SQL aggregate
      const { data: avgData } = await supabase
        .from('articles')
        .select('avg(relevance_score)')
        .eq('is_duplicate', false)
        .not('relevance_score', 'is', null)
        .single()

      const avg_relevance_score = Number(avgData?.avg || 0)

      return transformStats({
        totalArticles: totalResult.count || 0,
        sourceBreakdown: articles_by_source,
        categoryBreakdown: articles_by_category,
        avgRelevance: avg_relevance_score,
        last24h: last24hResult.count || 0,
        lastWeek: lastWeekResult.count || 0,
      })
    } catch (error: unknown) {
      throw new Error(`Stats query failed: ${transformDatabaseError(error)}`)
    }
  },

  /**
   * Get source metadata with statistics.
   */
  async getSourcesMetadata(): Promise<SourceMetadata[]> {
    try {
      const { data, error } = await supabase
        .from('articles')
        .select('source, relevance_score, published_at')
        .eq('is_duplicate', false)

      if (error) {
        throw new Error(`Failed to fetch source metadata: ${transformDatabaseError(error)}`)
      }

      // Group by source and calculate statistics
      const sourceStats: Record<string, {
        count: number
        lastPublished: string
        totalRelevance: number
        relevanceCount: number
      }> = {}

      data?.forEach(article => {
        const source = article.source
        if (!sourceStats[source]) {
          sourceStats[source] = {
            count: 0,
            lastPublished: article.published_at,
            totalRelevance: 0,
            relevanceCount: 0
          }
        }

        sourceStats[source].count += 1
        
        // Track most recent publication
        if (article.published_at > sourceStats[source].lastPublished) {
          sourceStats[source].lastPublished = article.published_at
        }

        // Sum relevance scores
        if (article.relevance_score !== null) {
          sourceStats[source].totalRelevance += article.relevance_score
          sourceStats[source].relevanceCount += 1
        }
      })

      // Transform to SourceMetadata array
      return Object.entries(sourceStats).map(([source, stats]) => {
        const avgRelevance = stats.relevanceCount > 0 
          ? stats.totalRelevance / stats.relevanceCount 
          : 0

        return transformSourceMetadata(
          source,
          stats.count,
          stats.lastPublished,
          avgRelevance
        )
      }).sort((a, b) => b.article_count - a.article_count) // Sort by article count descending
      
    } catch (error: unknown) {
      throw new Error(`Source metadata query failed: ${transformDatabaseError(error)}`)
    }
  },
}

// Export individual functions for direct use if needed
export const {
  getArticles,
  getArticlesBySource,
  getArticle,
  searchArticles,
  filterArticles,
  getSimilarArticles,
  getLatestDigest,
  getDigestById,
  getDigestSummaries,
  getStats,
  getSourcesMetadata,
} = supabaseQueries