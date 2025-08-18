import { Database } from '@/types/database'
import { Article, Digest, Stats, DigestSummary, SourceMetadata } from '@/types'

type ArticleRow = Database['public']['Tables']['articles']['Row']
type DigestRow = Database['public']['Tables']['daily_digests']['Row']

/**
 * Transform a database article row to frontend Article interface.
 * 
 * Args:
 *   row: Raw database row from articles table
 * 
 * Returns:
 *   Article: Transformed article object matching frontend interface
 */
export function transformArticleRow(row: ArticleRow): Article {
  return {
    id: row.id,
    title: row.title,
    url: row.url,
    source: row.source, // enum will be string
    summary: row.summary || '',
    relevance_score: row.relevance_score || 0,
    categories: row.categories || [],
    published_at: row.published_at,
    created_at: row.fetched_at,
    updated_at: row.fetched_at,
    author: row.author || undefined,
    content: row.content,
    tags: row.key_points || [],
    // Optional fields that may be added later
    thumbnail: undefined,
    image_url: undefined,
    comments_count: undefined,
  }
}

/**
 * Transform a database article row (projected columns) to frontend Article interface.
 * This is for list views that don't fetch full article content.
 * 
 * Args:
 *   row: Raw database row with projected columns (without content, author, etc.)
 * 
 * Returns:
 *   Article: Frontend article interface with defaults for missing fields
 */
export function transformArticleProjectedRow(row: {
  id: string
  title: string
  url: string
  source: string
  summary: string | null
  relevance_score: number | null
  categories: string[] | null
  published_at: string
  fetched_at: string
}): Article {
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
    author: undefined,
    content: '', // Not fetched in projected queries
    tags: [],
    // Optional fields that may be added later
    thumbnail: undefined,
    image_url: undefined,
    comments_count: undefined,
  }
}

/**
 * Transform a database digest row to frontend Digest interface.
 * 
 * Args:
 *   row: Raw database row from daily_digests table
 *   articles: Array of articles included in this digest
 * 
 * Returns:
 *   Digest: Transformed digest object matching frontend interface
 */
export function transformDigestRow(row: DigestRow, articles: Article[] = []): Digest {
  const digestDate = new Date(row.digest_date)
  
  return {
    id: row.id,
    title: `Daily Digest - ${digestDate.toLocaleDateString('en-US', { 
      year: 'numeric', 
      month: 'long', 
      day: 'numeric' 
    })}`,
    summary: row.summary_text,
    key_points: [], // Could be extracted from summary_text if needed
    audio_url: row.audio_url || '',
    duration: row.audio_duration || 0,
    articles,
    created_at: row.created_at,
  }
}

/**
 * Transform a database digest row to frontend DigestSummary interface.
 * Used for digest list pages where full article arrays aren't needed.
 * 
 * Args:
 *   row: Raw database row from daily_digests table
 * 
 * Returns:
 *   DigestSummary: Lightweight digest object for list views
 */
export function transformDigestToSummary(row: DigestRow): DigestSummary {
  // const digestDate = new Date(row.digest_date)
  
  return {
    id: row.id,
    date: row.digest_date,
    title: `Daily AI News Digest`,
    summary: row.summary_text,
    key_developments: [], // Could extract from summary if needed
    article_count: row.total_articles_processed,
    audio_url: row.audio_url || undefined,
    audio_duration: row.audio_duration || undefined,
  }
}

/**
 * Transform source statistics to SourceMetadata interface.
 * 
 * Args:
 *   source: Source name (enum value)
 *   count: Number of articles from this source
 *   lastPublished: ISO string of most recent article
 *   avgRelevance: Average relevance score
 * 
 * Returns:
 *   SourceMetadata: Source information for display
 */
export function transformSourceMetadata(
  source: string,
  count: number,
  lastPublished?: string,
  avgRelevance: number = 0
): SourceMetadata {
  // Source display configuration
  const sourceConfig: Record<string, { display_name: string; description: string; icon_url: string }> = {
    arxiv: {
      display_name: 'ArXiv',
      description: 'Academic papers and preprints in AI, ML, and computer science',
      icon_url: '/icons/arxiv.svg'
    },
    hackernews: {
      display_name: 'Hacker News',
      description: 'Community-driven tech news and discussions',
      icon_url: '/icons/hackernews.svg'
    },
    rss: {
      display_name: 'RSS Feeds',
      description: 'Curated RSS feeds from AI blogs and news sites',
      icon_url: '/icons/rss.svg'
    },
    youtube: {
      display_name: 'YouTube',
      description: 'AI-related video content and tutorials',
      icon_url: '/icons/youtube.svg'
    },
    reddit: {
      display_name: 'Reddit',
      description: 'AI community discussions and news',
      icon_url: '/icons/reddit.svg'
    },
    github: {
      display_name: 'GitHub',
      description: 'AI project releases and repository updates',
      icon_url: '/icons/github.svg'
    },
    huggingface: {
      display_name: 'Hugging Face',
      description: 'Model releases, datasets, and community updates',
      icon_url: '/icons/huggingface.svg'
    }
  }
  
  const config = sourceConfig[source] || {
    display_name: source,
    description: 'AI news and updates',
    icon_url: '/icons/default.svg'
  }
  
  return {
    name: source,
    display_name: config.display_name,
    description: config.description,
    article_count: count,
    last_published: lastPublished,
    avg_relevance_score: avgRelevance,
    status: count > 0 ? 'active' : 'inactive',
    icon_url: config.icon_url,
  }
}

/**
 * Transform raw statistics data to Stats interface.
 * 
 * Args:
 *   data: Object containing various database counts and aggregations
 * 
 * Returns:
 *   Stats: Formatted statistics for dashboard display
 */
export function transformStats(data: {
  totalArticles: number
  sourceBreakdown: Record<string, number>
  categoryBreakdown: Record<string, number>
  avgRelevance: number
  last24h: number
  lastWeek: number
}): Stats {
  return {
    total_articles: data.totalArticles,
    articles_by_source: data.sourceBreakdown,
    articles_by_category: data.categoryBreakdown,
    avg_relevance_score: data.avgRelevance,
    articles_last_24h: data.last24h,
    articles_last_week: data.lastWeek,
  }
}

/**
 * Transform database error to user-friendly message.
 * 
 * Args:
 *   error: Database error object
 * 
 * Returns:
 *   string: User-friendly error message
 */
export function transformDatabaseError(error: unknown): string {
  if (error && typeof error === 'object' && 'code' in error) {
    const errorWithCode = error as { code: string; message?: string }
    
    if (errorWithCode.code === 'PGRST301') {
      return 'No results found for your search criteria'
    }
    
    if (errorWithCode.code === 'PGRST116') {
      return 'No data available'
    }
  }
  
  if (error && typeof error === 'object' && 'message' in error) {
    const errorWithMessage = error as { message: string }
    
    if (errorWithMessage.message?.includes('JWT')) {
      return 'Authentication expired. Please refresh the page.'
    }
    
    if (errorWithMessage.message?.includes('connection')) {
      return 'Unable to connect to database. Please check your connection.'
    }
    
    if (errorWithMessage.message?.includes('timeout')) {
      return 'Request timed out. Please try again.'
    }
    
    return errorWithMessage.message
  }
  
  // Generic fallback
  return 'An unexpected error occurred'
}

/**
 * Validate article data completeness for display.
 * 
 * Args:
 *   article: Article object to validate
 * 
 * Returns:
 *   boolean: True if article has minimum required fields
 */
export function validateArticleData(article: Partial<Article>): article is Article {
  return !!(
    article.id &&
    article.title &&
    article.url &&
    article.source &&
    article.published_at
  )
}