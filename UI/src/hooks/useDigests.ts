"use client"

import useSWR, { SWRResponse } from "swr"
import { Digest, DigestSummary } from "@/types"

export interface DigestsParams {
  page?: number
  perPage?: number
  startDate?: string
  endDate?: string
}

export interface DigestsResponse {
  digests: DigestSummary[]
  total: number
  page: number
  perPage: number
  totalPages: number
}

export interface DigestDetailResponse {
  digest: Digest
}

export interface UseDigestsReturn extends SWRResponse<DigestsResponse> {
  digests: DigestSummary[]
  total: number
  page: number
  perPage: number
  totalPages: number
}

export interface UseDigestDetailReturn extends SWRResponse<DigestDetailResponse> {
  digest?: Digest
}

/**
 * Hook for fetching paginated digest summaries
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

  // Build query parameters
  const queryParams = new URLSearchParams()
  queryParams.set("page", String(page))
  queryParams.set("per_page", String(perPage))
  if (startDate) queryParams.set("start_date", startDate)
  if (endDate) queryParams.set("end_date", endDate)

  const key = `/digests?${queryParams.toString()}`

  const { data, error, isLoading, mutate, isValidating } = useSWR<DigestsResponse>(key)

  return {
    data,
    error,
    isLoading,
    mutate,
    isValidating,
    digests: data?.digests ?? [],
    total: data?.total ?? 0,
    page: data?.page ?? page,
    perPage: data?.perPage ?? perPage,
    totalPages: data?.totalPages ?? 0
  }
}

/**
 * Hook for fetching a single digest by ID
 * 
 * @param id The digest ID to fetch
 * @returns Digest detail data with loading and error states
 */
export function useDigestDetail(id?: string): UseDigestDetailReturn {
  const key = id ? `/digests/${id}` : null

  const { data, error, isLoading, mutate, isValidating } = useSWR<DigestDetailResponse>(
    key,
    {
      revalidateOnFocus: false,
      revalidateOnReconnect: false
    }
  )

  return {
    data,
    error,
    isLoading,
    mutate,
    isValidating,
    digest: data?.digest
  }
}

/**
 * Hook for fetching the latest digest
 * 
 * @returns Latest digest data with loading and error states
 */
export function useLatestDigest(): UseDigestDetailReturn {
  const key = "/digests/latest"

  const { data, error, isLoading, mutate, isValidating } = useSWR<DigestDetailResponse>(
    key,
    {
      revalidateOnFocus: false,
      revalidateOnReconnect: false,
      refreshInterval: 60000 // Refresh every minute
    }
  )

  return {
    data,
    error,
    isLoading,
    mutate,
    isValidating,
    digest: data?.digest
  }
}

/**
 * Hook for fetching today's digest
 * 
 * @returns Today's digest data with loading and error states
 */
export function useTodayDigest(): UseDigestDetailReturn {
  const today = new Date().toISOString().split("T")[0]
  const key = `/digests/date/${today}`

  const { data, error, isLoading, mutate, isValidating } = useSWR<DigestDetailResponse>(
    key,
    {
      revalidateOnFocus: false,
      revalidateOnReconnect: false,
      refreshInterval: 300000 // Refresh every 5 minutes
    }
  )

  return {
    data,
    error,
    isLoading,
    mutate,
    isValidating,
    digest: data?.digest
  }
}

/**
 * Hook for fetching digest audio metadata
 * 
 * @param digestId The digest ID to fetch audio for
 * @returns Audio metadata with loading and error states
 */
export function useDigestAudio(digestId?: string) {
  const key = digestId ? `/digests/${digestId}/audio` : null

  interface AudioResponse {
    url: string
    duration: number
    format: string
    size: number
  }

  const { data, error, isLoading, mutate, isValidating } = useSWR<AudioResponse>(
    key,
    {
      revalidateOnFocus: false,
      revalidateOnReconnect: false
    }
  )

  return {
    data,
    error,
    isLoading,
    mutate,
    isValidating,
    audioUrl: data?.url,
    duration: data?.duration,
    format: data?.format,
    size: data?.size
  }
}

/**
 * Prefetch digests data
 * Useful for preloading data before navigation
 */
export async function prefetchDigests(params: DigestsParams = {}) {
  const {
    page = 1,
    perPage = 10,
    startDate,
    endDate
  } = params

  const queryParams = new URLSearchParams()
  queryParams.set("page", String(page))
  queryParams.set("per_page", String(perPage))
  if (startDate) queryParams.set("start_date", startDate)
  if (endDate) queryParams.set("end_date", endDate)

  const url = `/api/v1/digests?${queryParams.toString()}`
  
  try {
    const response = await fetch(url)
    if (!response.ok) {
      throw new Error(`Failed to prefetch digests: ${response.statusText}`)
    }
    return await response.json()
  } catch (error) {
    console.error("Error prefetching digests:", error)
    return null
  }
}

/**
 * Prefetch a single digest by ID
 */
export async function prefetchDigest(id: string) {
  const url = `/api/v1/digests/${id}`
  
  try {
    const response = await fetch(url)
    if (!response.ok) {
      throw new Error(`Failed to prefetch digest: ${response.statusText}`)
    }
    return await response.json()
  } catch (error) {
    console.error("Error prefetching digest:", error)
    return null
  }
}