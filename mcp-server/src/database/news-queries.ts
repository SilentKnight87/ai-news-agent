import { withDatabase } from './utils';

export interface ArticleFilters {
  source?: string;
  limit?: number;
  offset?: number;
  since?: Date;
  minRelevanceScore?: number;
}

export interface SearchResult {
  articles: any[];
  total: number;
}

export interface DigestResult {
  digests: any[];
  total: number;
}

/**
 * Search articles using full-text search
 * Ported from: src/repositories/articles.py:search_articles()
 */
export async function searchArticles(
  databaseUrl: string, 
  query: string, 
  filters?: ArticleFilters
): Promise<SearchResult> {
  return withDatabase(databaseUrl, async (db) => {
    // Build dynamic query similar to Python implementation
    const conditions = ['to_tsvector(title || \' \' || content) @@ plainto_tsquery($1)'];
    const params: any[] = [query];
    
    if (filters?.source) {
      conditions.push(`source = $${params.length + 1}`);
      params.push(filters.source);
    }
    
    if (filters?.minRelevanceScore) {
      conditions.push(`relevance_score >= $${params.length + 1}`);
      params.push(filters.minRelevanceScore);
    }
    
    if (filters?.since) {
      conditions.push(`published_at >= $${params.length + 1}`);
      params.push(filters.since);
    }
    
    const whereClause = conditions.join(' AND ');
    const limit = filters?.limit || 20;
    const offset = filters?.offset || 0;
    
    // Get total count
    const countResult = await db.unsafe(
      `SELECT COUNT(*) as count FROM articles WHERE ${whereClause}`,
      params
    );
    
    // Get paginated results
    const articles = await db.unsafe(
      `SELECT 
         id, source_id, source, title, content, url, author, 
         published_at, fetched_at, summary, relevance_score, 
         categories, key_points, is_duplicate, duplicate_of
       FROM articles 
       WHERE ${whereClause}
       ORDER BY published_at DESC
       LIMIT $${params.length + 1} OFFSET $${params.length + 2}`,
      [...params, limit, offset]
    );
    
    return { 
      articles, 
      total: parseInt(countResult[0].count) 
    };
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
      SELECT 
        id, source_id, source, title, content, url, author, 
        published_at, fetched_at, summary, relevance_score, 
        categories, key_points, is_duplicate, duplicate_of
      FROM articles 
      WHERE published_at >= $1
      AND is_duplicate = false
    `;
    const params: any[] = [since];
    
    if (filters?.source) {
      query += ` AND source = $${params.length + 1}`;
      params.push(filters.source);
    }
    
    if (filters?.minRelevanceScore) {
      query += ` AND relevance_score >= $${params.length + 1}`;
      params.push(filters.minRelevanceScore);
    }
    
    const limit = filters?.limit || 50;
    params.push(limit);
    query += ` ORDER BY published_at DESC LIMIT $${params.length}`;
    
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
        COALESCE(AVG(relevance_score), 0) as avg_relevance
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
): Promise<DigestResult> {
  return withDatabase(databaseUrl, async (db) => {
    const offset = (page - 1) * perPage;
    
    const countResult = await db.unsafe(
      'SELECT COUNT(*) as count FROM daily_digests'
    );
    
    const digests = await db.unsafe(`
      SELECT 
        id, digest_date, summary_text, total_articles_processed,
        audio_url, audio_duration, created_at,
        (SELECT COUNT(*) FROM digest_articles WHERE digest_id = daily_digests.id) as article_count
      FROM daily_digests
      ORDER BY digest_date DESC
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
      SELECT 
        id, digest_date, summary_text, total_articles_processed,
        audio_url, audio_duration, audio_size, voice_type, audio_generated_at, created_at
      FROM daily_digests 
      WHERE id = $1
    `, [digestId]);
    
    if (!digest.length) return null;
    
    const articles = await db.unsafe(`
      SELECT 
        a.id, a.source_id, a.source, a.title, a.content, a.url, a.author,
        a.published_at, a.fetched_at, a.summary, a.relevance_score,
        a.categories, a.key_points, a.is_duplicate, a.duplicate_of
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
        COALESCE(AVG(relevance_score), 0) as avg_relevance_score,
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
    'github_trending': 'GitHub Trending',
    'rss': 'RSS Feeds'
  };
  return displayNames[source] || source;
}

function getSourceDescription(source: string): string {
  const descriptions: Record<string, string> = {
    'arxiv': 'Latest AI/ML research papers',
    'hackernews': 'Tech news and discussions',
    'reddit_machinelearning': 'ML community discussions',
    'reddit_locallama': 'Open source LLM discussions',
    'github_trending': 'Trending AI/ML repositories',
    'rss': 'RSS feed aggregations'
  };
  return descriptions[source] || 'AI/ML news source';
}