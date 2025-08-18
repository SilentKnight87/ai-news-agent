"use client"

import useSWR, { SWRResponse } from "swr"
import { supabaseQueries } from "@/lib/supabase-queries"
import { Digest, DigestSummary, PaginationMeta } from "@/types"

export interface DigestsParams {
  page?: number
  perPage?: number
  startDate?: string
  endDate?: string
}

export interface DigestsResponse {
  digests: DigestSummary[]
  pagination: PaginationMeta
}

export interface UseDigestsReturn extends SWRResponse<DigestsResponse> {
  digests: DigestSummary[]
  total: number
  page: number
  perPage: number
  totalPages: number
}

export interface UseDigestDetailReturn extends SWRResponse<Digest | null> {
  digest?: Digest | null
}

/**
 * Hook for fetching paginated digest summaries.
 * Migrated to use direct Supabase access instead of API.
 * 
 * @param params Query parameters for filtering and pagination
 * @returns Digests data with loading and error states
 */
export function useDigests(params: DigestsParams = {}): UseDigestsReturn {
  const {
    page = 1,
    perPage = 10,
    startDate,
    endDate
  } = params

  // Create cache key
  const cacheKey = ['digests', JSON.stringify(params)]

  const { data, error, isLoading, mutate, isValidating } = useSWR<DigestsResponse>(
    cacheKey,
    () => supabaseQueries.getDigestSummaries({
      page,
      per_page: perPage,
    }),
    {
      revalidateOnFocus: false,
      revalidateOnReconnect: true,
      refreshInterval: 300000, // Refresh every 5 minutes
      errorRetryCount: 2,
    }
  )

  return {
    data,
    error,
    isLoading,
    mutate,
    isValidating,
    digests: data?.digests ?? [],
    total: data?.pagination?.total ?? 0,
    page: data?.pagination?.page ?? page,
    perPage: data?.pagination?.per_page ?? perPage,
    totalPages: data?.pagination?.total_pages ?? 0
  }
}

/**
 * Hook for fetching a single digest by ID.
 * Migrated to use direct Supabase access instead of API.
 * 
 * @param id The digest ID to fetch
 * @returns Digest detail data with loading and error states
 */
export function useDigestDetail(id?: string): UseDigestDetailReturn {
  const key = id ? ['digest', id] : null

  const { data, error, isLoading, mutate, isValidating } = useSWR<Digest | null>(
    key,
    () => supabaseQueries.getDigestById(id!),
    {
      revalidateOnFocus: false,
      revalidateOnReconnect: false,
      errorRetryCount: 2,
    }
  )

  return {
    data,
    error,
    isLoading,
    mutate,
    isValidating,
    digest: data || undefined
  }
}

/**
 * Hook for fetching the latest digest.
 * Migrated to use direct Supabase access instead of API.
 * 
 * @returns Latest digest data with loading and error states
 */
export function useLatestDigest(): UseDigestDetailReturn {
  const key = 'digest-latest'

  const { data, error, isLoading, mutate, isValidating } = useSWR<Digest | null>(
    key,
    supabaseQueries.getLatestDigest,
    {
      revalidateOnFocus: false,
      revalidateOnReconnect: false,
      refreshInterval: 60000, // Refresh every minute
      errorRetryCount: 2,
    }
  )

  return {
    data,
    error,
    isLoading,
    mutate,
    isValidating,
    digest: data || undefined
  }
}

/**
 * Hook for fetching today's digest.
 * Note: This now uses the latest digest since date-based queries
 * require more complex filtering logic.
 * 
 * @returns Today's digest data with loading and error states
 */
export function useTodayDigest(): UseDigestDetailReturn {
  // For now, this returns the latest digest
  // TODO: Add date filtering to supabase queries if needed
  return useLatestDigest()
}

/**
 * Hook for fetching digest audio metadata.
 * Note: Audio metadata is now included in the digest object directly.
 * 
 * @param digestId The digest ID to fetch audio for
 * @returns Audio metadata with loading and error states
 */
export function useDigestAudio(digestId?: string) {
  const { data: digest, error, isLoading, mutate, isValidating } = useDigestDetail(digestId)

  return {
    data: digest ? {
      url: digest.audio_url,
      duration: digest.duration,
      format: 'mp3', // Default format
      size: 0, // Not available in current schema
    } : undefined,
    error,
    isLoading,
    mutate,
    isValidating,
    audioUrl: digest?.audio_url,
    duration: digest?.duration,
    format: 'mp3',
    size: 0,
  }
}

/**
 * Prefetch digests data using Supabase queries.
 * Useful for preloading data before navigation.
 */
export async function prefetchDigests(params: DigestsParams = {}) {
  const {
    page = 1,
    perPage = 10,
  } = params

  try {
    const result = await supabaseQueries.getDigestSummaries({
      page,
      per_page: perPage,
    })
    return result
  } catch (error) {
    console.error("Error prefetching digests:", error)
    return null
  }
}

/**
 * Prefetch a single digest by ID using Supabase queries.
 */
export async function prefetchDigest(id: string) {
  try {
    const result = await supabaseQueries.getDigestById(id)
    return result
  } catch (error) {
    console.error("Error prefetching digest:", error)
    return null
  }
}