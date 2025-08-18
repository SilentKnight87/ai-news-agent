import useSWR from "swr";
import { supabaseQueries } from "@/lib/supabase-queries";
import { SearchResponse } from "@/types";

/**
 * useSearch
 * Migrated to use direct Supabase access instead of API.
 * - Debounce at the caller with useDebounce
 * - Always call useSWR exactly once; use null key to disable fetching
 */
export function useSearch(
  query?: string, 
  source?: string, 
  limit: number = 20, 
  offset: number = 0,
  relevance_min?: number
) {
  // Don't search if query is too short
  const shouldSearch = query && query.trim().length >= 2
  const searchOptions = {
    limit,
    offset,
    source,
    relevance_min,
  }
  
  const key = shouldSearch 
    ? ['search', query.trim(), JSON.stringify(searchOptions)]
    : null

  const { data, error, isLoading, mutate } = useSWR<SearchResponse>(
    key,
    () => supabaseQueries.searchArticles(query!.trim(), searchOptions),
    {
      revalidateOnFocus: false,
      revalidateOnReconnect: false,
      refreshInterval: 0,
      dedupingInterval: 30000, // Cache search results for 30 seconds
      errorRetryCount: 2,
      errorRetryInterval: 3000,
    }
  )

  return { data, error, isLoading, mutate }
}