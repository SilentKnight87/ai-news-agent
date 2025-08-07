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
  author?: string
  content?: string
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