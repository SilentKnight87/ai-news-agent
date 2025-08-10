import useSWR from "swr";
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
 * Fetches /api/v1/articles with page/per_page/sort_by/order/source
 * Uses global SWR fetcher (see ClientProviders)
 */
export function usePaginatedArticles(pagination: PaginationState): UsePaginatedArticlesResult {
  const params = new URLSearchParams();
  params.set("page", String(pagination.page));
  params.set("per_page", String(pagination.perPage));
  params.set("sort_by", pagination.sortBy);
  params.set("order", pagination.order);
  if (pagination.source) params.set("source", pagination.source);

  const key = `/articles?${params.toString()}`;

  const { data, error, mutate } = useSWR<PaginatedArticleResponse>(key);

  return {
    articles: data?.articles ?? [],
    pagination: data?.pagination,
    meta: data?.meta,
    isLoading: !error && !data,
    error,
    mutate,
  };
}