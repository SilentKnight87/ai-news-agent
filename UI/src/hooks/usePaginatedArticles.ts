import useSWR from "swr";
import { supabaseQueries } from "@/lib/supabase-queries";
import {
  Article,
  PaginatedArticleResponse,
  PaginationMeta,
  SortField,
  SortOrder,
} from "@/types";

export interface PaginationState {
  page: number;
  perPage: number;
  sortBy: SortField;
  order: SortOrder;
  source?: string;
  relevance_min?: number;
  category?: string;
  time_range?: string;
}

export interface UsePaginatedArticlesResult {
  articles: Article[];
  pagination?: PaginationMeta;
  meta?: Record<string, unknown>;
  isLoading: boolean;
  error?: unknown;
  mutate: (data?: PaginatedArticleResponse | Promise<PaginatedArticleResponse> | undefined, shouldRevalidate?: boolean) => Promise<PaginatedArticleResponse | undefined>;
}

/**
 * usePaginatedArticles
 * Migrated to use direct Supabase access instead of API.
 * Fetches articles with pagination and filtering support.
 */
export function usePaginatedArticles(pagination: PaginationState): UsePaginatedArticlesResult {
  // Create cache key from pagination state
  const cacheKey = ['paginated-articles', JSON.stringify(pagination)];

  const { data, error, mutate } = useSWR<PaginatedArticleResponse>(
    cacheKey,
    () => {
      if (pagination.source) {
        return supabaseQueries.getArticlesBySource(pagination.source, {
          page: pagination.page,
          per_page: pagination.perPage,
          relevance_min: pagination.relevance_min,
        });
      } else {
        return supabaseQueries.getArticles({
          page: pagination.page,
          per_page: pagination.perPage,
          sort_by: pagination.sortBy,
          order: pagination.order,
          relevance_min: pagination.relevance_min,
          category: pagination.category,
          time_range: pagination.time_range,
        });
      }
    },
    {
      revalidateOnFocus: false,
      revalidateOnReconnect: true,
      refreshInterval: 300000, // Refresh every 5 minutes
      dedupingInterval: 60000, // Dedupe requests within 1 minute
      errorRetryCount: 3,
      errorRetryInterval: 5000,
    }
  );

  return {
    articles: data?.articles ?? [],
    pagination: data?.pagination,
    meta: data?.meta,
    isLoading: !error && !data,
    error,
    mutate,
  };
}