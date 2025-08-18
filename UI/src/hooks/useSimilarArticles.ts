import useSWR from 'swr'
import { supabaseQueries } from '@/lib/supabase-queries'
import { Article } from '@/types'

/**
 * Hook for fetching articles similar to a given article.
 * Uses pgvector similarity search when available, falls back to category matching.
 * 
 * Args:
 *   articleId: ID of the article to find similar articles for
 *   options: Configuration options for similarity search
 * 
 * Returns:
 *   SWR response with similar articles data
 */
export function useSimilarArticles(
  articleId: string,
  options: { 
    limit?: number
    threshold?: number
    enabled?: boolean
  } = {}
) {
  const { enabled = true, ...similarOptions } = options
  
  const cacheKey = enabled && articleId 
    ? ['similar-articles', articleId, JSON.stringify(similarOptions)] 
    : null
  
  return useSWR(
    cacheKey,
    () => supabaseQueries.getSimilarArticles(articleId, similarOptions),
    {
      revalidateOnFocus: false,
      refreshInterval: 0,
      dedupingInterval: 600000, // Cache for 10 minutes
      errorRetryCount: 1, // Vector search might fail, don't retry too much
      onError: (error) => {
        console.warn('Similar articles search failed:', error.message)
      },
    }
  )
}

/**
 * Hook for prefetching similar articles.
 * Useful for preloading related content.
 * 
 * Args:
 *   articleId: ID of the article to find similar articles for
 *   options: Configuration options for similarity search
 */
export async function prefetchSimilarArticles(
  articleId: string,
  options: { 
    limit?: number
    threshold?: number
  } = {}
) {
  try {
    const result = await supabaseQueries.getSimilarArticles(articleId, options)
    return result
  } catch (error) {
    console.error('Error prefetching similar articles:', error)
    return null
  }
}