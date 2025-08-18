import useSWR from 'swr'
import { supabaseQueries } from '@/lib/supabase-queries'
import { SourceMetadata } from '@/types'

/**
 * Hook for fetching source metadata and statistics.
 * Provides information about all available news sources.
 * 
 * Returns:
 *   SWR response with source metadata array
 */
export function useSources() {
  return useSWR<SourceMetadata[]>(
    'sources',
    supabaseQueries.getSourcesMetadata,
    {
      revalidateOnFocus: false,
      revalidateOnReconnect: true,
      refreshInterval: 600000, // Refresh every 10 minutes
      dedupingInterval: 300000, // Cache for 5 minutes
      errorRetryCount: 2,
      onError: (error) => {
        console.error('useSources error:', error.message)
      },
    }
  )
}

/**
 * Hook for getting a specific source's metadata by name.
 * 
 * Args:
 *   sourceName: The name of the source to get metadata for
 * 
 * Returns:
 *   Source metadata object or undefined if not found
 */
export function useSource(sourceName: string) {
  const { data: sources, error, isLoading } = useSources()
  
  const source = sources?.find(s => s.name === sourceName)
  
  return {
    data: source,
    error,
    isLoading,
    exists: !!source,
  }
}

/**
 * Hook for getting active sources (sources with articles).
 * 
 * Returns:
 *   Array of sources that have at least one article
 */
export function useActiveSources() {
  const { data: sources, error, isLoading } = useSources()
  
  const activeSources = sources?.filter(s => s.status === 'active') || []
  
  return {
    data: activeSources,
    error,
    isLoading,
    count: activeSources.length,
  }
}