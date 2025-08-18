import useSWR from 'swr'
import { supabaseQueries } from '@/lib/supabase-queries'
import { useErrorDisplay } from './useSupabaseError'
import { ArticleFilters, PaginatedArticleResponse } from '@/types'

/**
 * Hook for fetching articles with filtering and pagination.
 * Migrated to use direct Supabase access instead of API.
 */
export function useArticles(
  source?: string, 
  filters?: ArticleFilters & { 
    page?: number
    per_page?: number
    sort_by?: 'published_at' | 'relevance_score' | 'title' | 'fetched_at'
    order?: 'asc' | 'desc'
  }
) {
  const { shouldShowRetry, getDisplayMessage } = useErrorDisplay()
  
  // Create stable cache key
  const cacheKey = source
    ? ['articles', source, filters]
    : ['articles', filters]
  
  return useSWR<PaginatedArticleResponse>(
    cacheKey,
    () => {
      if (source) {
        return supabaseQueries.getArticlesBySource(source, {
          page: filters?.page,
          per_page: filters?.per_page,
          relevance_min: filters?.relevance_min,
        })
      } else {
        return supabaseQueries.getArticles(filters || {})
      }
    },
    {
      revalidateOnFocus: false,
      revalidateOnReconnect: true,
      refreshInterval: 300000, // Refresh every 5 minutes
      dedupingInterval: 60000, // Dedupe requests within 1 minute
      errorRetryCount: 3,
      errorRetryInterval: 5000,
      onError: (error) => {
        console.warn('useArticles error:', getDisplayMessage(error))
      },
    }
  )
}

/**
 * Hook for fetching a single article by ID.
 * Migrated to use direct Supabase access.
 */
export function useArticle(id: string) {
  const { getDisplayMessage } = useErrorDisplay()
  
  return useSWR(
    id ? ['article', id] : null,
    () => supabaseQueries.getArticle(id),
    {
      revalidateOnFocus: false,
      revalidateOnReconnect: true,
      refreshInterval: 0, // Don't auto-refresh individual articles
      dedupingInterval: 300000, // Cache for 5 minutes
      errorRetryCount: 2,
      onError: (error) => {
        console.warn('useArticle error:', getDisplayMessage(error))
      },
    }
  )
}

/**
 * Hook for fetching the latest digest.
 * Migrated to use direct Supabase access.
 */
export function useDigest() {
  const { getDisplayMessage } = useErrorDisplay()
  
  return useSWR('digest', supabaseQueries.getLatestDigest, {
    refreshInterval: 60000, // Refresh every minute
    revalidateOnFocus: false,
    errorRetryCount: 2,
    onError: (error) => {
      console.warn('useDigest error:', getDisplayMessage(error))
    },
  })
}

/**
 * Hook for fetching system statistics.
 * Migrated to use direct Supabase access.
 */
export function useStats() {
  const { getDisplayMessage } = useErrorDisplay()
  
  return useSWR('stats', supabaseQueries.getStats, {
    refreshInterval: 30000, // Refresh every 30 seconds
    revalidateOnFocus: false,
    errorRetryCount: 2,
    onError: (error) => {
      console.warn('useStats error:', getDisplayMessage(error))
    },
  })
}