"use client"

import { useState, useCallback, useEffect } from "react"
import { useRouter, useSearchParams } from "next/navigation"
import { FiltersApplied } from "@/types"

export interface FilterState extends FiltersApplied {
  // Additional filter properties
  query?: string
  sortBy?: "relevance_score" | "published_at" | "title"
  sortOrder?: "asc" | "desc"
}

interface UseFilterOptions {
  defaultFilters?: Partial<FilterState>
  syncWithUrl?: boolean
}

interface UseFilterReturn {
  filters: FilterState
  setFilter: <K extends keyof FilterState>(key: K, value: FilterState[K]) => void
  setFilters: (filters: Partial<FilterState>) => void
  resetFilters: () => void
  applyFilters: () => void
  hasActiveFilters: boolean
  filterCount: number
}

/**
 * Hook for managing filter state with optional URL synchronization
 * 
 * @param options Configuration options for the filter hook
 * @returns Filter state and management functions
 */
export function useFilter(options: UseFilterOptions = {}): UseFilterReturn {
  const {
    defaultFilters = {},
    syncWithUrl = true
  } = options

  const router = useRouter()
  const searchParams = useSearchParams()

  // Initialize filters from URL params or defaults
  const initializeFilters = useCallback((): FilterState => {
    if (!syncWithUrl) {
      return defaultFilters as FilterState
    }

    const filters: FilterState = { ...defaultFilters }

    // Parse URL parameters
    const startDate = searchParams.get("start_date")
    const endDate = searchParams.get("end_date")
    const relevanceMin = searchParams.get("relevance_min")
    const relevanceMax = searchParams.get("relevance_max")
    const sources = searchParams.get("sources")
    const categories = searchParams.get("categories")
    const query = searchParams.get("q")
    const sortBy = searchParams.get("sort_by")
    const sortOrder = searchParams.get("sort_order")

    if (startDate) filters.start_date = startDate
    if (endDate) filters.end_date = endDate
    if (relevanceMin) filters.relevance_min = parseFloat(relevanceMin)
    if (relevanceMax) filters.relevance_max = parseFloat(relevanceMax)
    if (sources) filters.sources = sources.split(",")
    if (categories) filters.categories = categories.split(",")
    if (query) filters.query = query
    if (sortBy) filters.sortBy = sortBy as FilterState["sortBy"]
    if (sortOrder) filters.sortOrder = sortOrder as FilterState["sortOrder"]

    return filters
  }, [searchParams, defaultFilters, syncWithUrl])

  const [filters, setFiltersState] = useState<FilterState>(initializeFilters)
  const [pendingFilters, setPendingFilters] = useState<FilterState>(filters)

  // Sync filters with URL when they change
  useEffect(() => {
    if (!syncWithUrl) return

    const params = new URLSearchParams()

    // Add filters to URL params
    if (filters.start_date) params.set("start_date", filters.start_date)
    if (filters.end_date) params.set("end_date", filters.end_date)
    if (filters.relevance_min !== undefined) params.set("relevance_min", String(filters.relevance_min))
    if (filters.relevance_max !== undefined) params.set("relevance_max", String(filters.relevance_max))
    if (filters.sources?.length) params.set("sources", filters.sources.join(","))
    if (filters.categories?.length) params.set("categories", filters.categories.join(","))
    if (filters.query) params.set("q", filters.query)
    if (filters.sortBy) params.set("sort_by", filters.sortBy)
    if (filters.sortOrder) params.set("sort_order", filters.sortOrder)

    const queryString = params.toString()
    const newUrl = queryString ? `?${queryString}` : window.location.pathname
    
    // Only update URL if it's different
    if (newUrl !== window.location.search) {
      router.replace(newUrl, { scroll: false })
    }
  }, [filters, router, syncWithUrl])

  // Set a single filter value
  const setFilter = useCallback(<K extends keyof FilterState>(
    key: K,
    value: FilterState[K]
  ) => {
    setPendingFilters(prev => ({
      ...prev,
      [key]: value
    }))
  }, [])

  // Set multiple filter values
  const setFilters = useCallback((newFilters: Partial<FilterState>) => {
    setPendingFilters(prev => ({
      ...prev,
      ...newFilters
    }))
  }, [])

  // Apply pending filters
  const applyFilters = useCallback(() => {
    setFiltersState(pendingFilters)
  }, [pendingFilters])

  // Reset all filters to defaults
  const resetFilters = useCallback(() => {
    const resetState = defaultFilters as FilterState
    setFiltersState(resetState)
    setPendingFilters(resetState)
  }, [defaultFilters])

  // Calculate if any filters are active
  const hasActiveFilters = Object.keys(filters).some(key => {
    const value = filters[key as keyof FilterState]
    if (Array.isArray(value)) return value.length > 0
    if (typeof value === "string") return value.length > 0
    if (typeof value === "number") return true
    return false
  })

  // Count active filters
  const filterCount = Object.keys(filters).reduce((count, key) => {
    const value = filters[key as keyof FilterState]
    if (Array.isArray(value) && value.length > 0) return count + 1
    if (typeof value === "string" && value.length > 0) return count + 1
    if (typeof value === "number") return count + 1
    return count
  }, 0)

  return {
    filters,
    setFilter,
    setFilters,
    resetFilters,
    applyFilters,
    hasActiveFilters,
    filterCount
  }
}