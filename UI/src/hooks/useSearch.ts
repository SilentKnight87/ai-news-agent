import useSWR from "swr";
import { SearchResponse } from "@/types";

/**
 * useSearch
 * - Debounce at the caller with useDebounce
 * - Always call useSWR exactly once; use null key to disable fetching
 */
export function useSearch(query?: string, source?: string, limit: number = 20, offset: number = 0) {
  const params = new URLSearchParams();
  if (query && query.trim().length > 0) {
    params.set("q", query.trim());
  }
  if (source) params.set("source", source);
  if (limit) params.set("limit", String(limit));
  if (offset) params.set("offset", String(offset));

  const key = params.has("q") ? `/articles/search?${params.toString()}` : null;

  const { data, error, isLoading, mutate } = useSWR<SearchResponse>(key);

  return { data, error, isLoading, mutate };
}