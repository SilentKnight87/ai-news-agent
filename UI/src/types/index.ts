export interface Article {
  id: string
  title: string
  url: string
  source: string
  summary: string
  relevance_score: number
  categories: string[]
  published_at: string
  created_at: string
  updated_at: string
  thumbnail?: string
  image_url?: string
  author?: string
  content?: string
  tags?: string[]
  comments_count?: number
}

export interface Digest {
  id: string
  title: string
  summary: string
  key_points: string[]
  audio_url: string
  duration: number
  articles: Article[]
  created_at: string
}

export interface ArticleParams {
  source?: string
  category?: string
  relevance_min?: number
  time_range?: string
  limit?: number
  offset?: number
}

export interface ArticleFilters {
  category?: string
  relevance_min?: number
  time_range?: string
}

export interface Stats {
  total_articles: number
  articles_by_source: Record<string, number>
  articles_by_category: Record<string, number>
  avg_relevance_score: number
  articles_last_24h: number
  articles_last_week: number
}
// ==== API response models per spec/frontend-api-integration.md ====

export interface SearchResponse {
  articles: Article[];
  total: number;
  query: string;
  took_ms: number;
}

// Structured filters applied, avoiding `any`
export interface FiltersApplied {
  start_date?: string;
  end_date?: string;
  relevance_min?: number;
  relevance_max?: number;
  sources?: string[];
  categories?: string[];
}

export type SortField = 'published_at' | 'relevance_score' | 'title' | 'fetched_at';
export type SortOrder = 'asc' | 'desc';

// Metadata for paginated responses
export interface ArticlesMeta {
  sort_by: SortField;
  order: SortOrder;
  cache_hit?: boolean;
  [key: string]: unknown;
}

export interface FilterResponse {
  articles: Article[];
  filters_applied: FiltersApplied;
  total: number;
  took_ms: number;
}

export interface PaginationMeta {
  page: number;
  per_page: number;
  total: number;
  total_pages: number;
  has_next: boolean;
  has_prev: boolean;
}

export interface PaginatedArticleResponse {
  articles: Article[];
  pagination: PaginationMeta;
  meta?: ArticlesMeta;
}

// Digest list item summary for digests index page
export interface DigestSummary {
  id: string;
  date: string; // ISO date string
  title: string;
  summary: string;
  key_developments: string[];
  article_count: number;
  audio_url?: string;
  audio_duration?: number;
}

// Source statistics for sources overview page
export interface SourceMetadata {
  name: string;
  display_name: string;
  description: string;
  article_count: number;
  last_fetch?: string;     // ISO datetime string
  last_published?: string; // ISO datetime string
  avg_relevance_score: number;
  status: 'active' | 'inactive';
  icon_url: string;
}