"use client"

import { useState, useCallback, useMemo } from "react"

export interface PaginationState {
  currentPage: number
  itemsPerPage: number
  totalItems: number
}

export interface UsePaginationOptions {
  initialPage?: number
  initialItemsPerPage?: number
  totalItems?: number
  itemsPerPageOptions?: number[]
}

export interface UsePaginationReturn {
  currentPage: number
  itemsPerPage: number
  totalItems: number
  totalPages: number
  hasNextPage: boolean
  hasPrevPage: boolean
  startIndex: number
  endIndex: number
  offset: number
  
  // Navigation functions
  nextPage: () => void
  prevPage: () => void
  goToPage: (page: number) => void
  goToFirstPage: () => void
  goToLastPage: () => void
  
  // Configuration functions
  setItemsPerPage: (items: number) => void
  setTotalItems: (total: number) => void
  
  // Utility functions
  getPageNumbers: (maxVisible?: number) => number[]
  getPaginatedItems: <T>(items: T[]) => T[]
}

/**
 * Hook for managing pagination state and navigation
 * 
 * @param options Configuration options for pagination
 * @returns Pagination state and control functions
 */
export function usePagination(options: UsePaginationOptions = {}): UsePaginationReturn {
  const {
    initialPage = 1,
    initialItemsPerPage = 20,
    totalItems: initialTotalItems = 0,
    itemsPerPageOptions = [10, 20, 50, 100]
  } = options

  const [currentPage, setCurrentPage] = useState(initialPage)
  const [itemsPerPage, setItemsPerPageState] = useState(initialItemsPerPage)
  const [totalItems, setTotalItemsState] = useState(initialTotalItems)

  // Calculate derived values
  const totalPages = useMemo(() => {
    return Math.max(1, Math.ceil(totalItems / itemsPerPage))
  }, [totalItems, itemsPerPage])

  const hasNextPage = currentPage < totalPages
  const hasPrevPage = currentPage > 1

  const startIndex = useMemo(() => {
    return (currentPage - 1) * itemsPerPage
  }, [currentPage, itemsPerPage])

  const endIndex = useMemo(() => {
    return Math.min(startIndex + itemsPerPage - 1, totalItems - 1)
  }, [startIndex, itemsPerPage, totalItems])

  const offset = startIndex

  // Navigation functions
  const nextPage = useCallback(() => {
    setCurrentPage(prev => Math.min(prev + 1, totalPages))
  }, [totalPages])

  const prevPage = useCallback(() => {
    setCurrentPage(prev => Math.max(prev - 1, 1))
  }, [])

  const goToPage = useCallback((page: number) => {
    const validPage = Math.max(1, Math.min(page, totalPages))
    setCurrentPage(validPage)
  }, [totalPages])

  const goToFirstPage = useCallback(() => {
    setCurrentPage(1)
  }, [])

  const goToLastPage = useCallback(() => {
    setCurrentPage(totalPages)
  }, [totalPages])

  // Configuration functions
  const setItemsPerPage = useCallback((items: number) => {
    if (!itemsPerPageOptions.includes(items) && items > 0) {
      console.warn(`Items per page value ${items} is not in allowed options:`, itemsPerPageOptions)
    }
    setItemsPerPageState(items)
    // Reset to first page when changing items per page
    setCurrentPage(1)
  }, [itemsPerPageOptions])

  const setTotalItems = useCallback((total: number) => {
    setTotalItemsState(Math.max(0, total))
    // Adjust current page if it exceeds new total pages
    const newTotalPages = Math.max(1, Math.ceil(total / itemsPerPage))
    if (currentPage > newTotalPages) {
      setCurrentPage(newTotalPages)
    }
  }, [currentPage, itemsPerPage])

  // Generate page numbers for pagination UI
  const getPageNumbers = useCallback((maxVisible = 7): number[] => {
    if (totalPages <= maxVisible) {
      return Array.from({ length: totalPages }, (_, i) => i + 1)
    }

    const halfVisible = Math.floor(maxVisible / 2)
    const pages: number[] = []

    // Always include first page
    pages.push(1)

    // Calculate start and end of visible range
    let start = Math.max(2, currentPage - halfVisible)
    let end = Math.min(totalPages - 1, currentPage + halfVisible)

    // Adjust range if at the beginning or end
    if (currentPage <= halfVisible + 1) {
      end = Math.min(totalPages - 1, maxVisible - 2)
    } else if (currentPage >= totalPages - halfVisible) {
      start = Math.max(2, totalPages - maxVisible + 3)
    }

    // Add ellipsis if needed
    if (start > 2) {
      pages.push(-1) // -1 represents ellipsis
    }

    // Add visible page numbers
    for (let i = start; i <= end; i++) {
      pages.push(i)
    }

    // Add ellipsis if needed
    if (end < totalPages - 1) {
      pages.push(-1) // -1 represents ellipsis
    }

    // Always include last page
    if (totalPages > 1) {
      pages.push(totalPages)
    }

    return pages
  }, [currentPage, totalPages])

  // Get paginated items from an array
  const getPaginatedItems = useCallback(<T,>(items: T[]): T[] => {
    return items.slice(startIndex, endIndex + 1)
  }, [startIndex, endIndex])

  return {
    currentPage,
    itemsPerPage,
    totalItems,
    totalPages,
    hasNextPage,
    hasPrevPage,
    startIndex,
    endIndex,
    offset,
    nextPage,
    prevPage,
    goToPage,
    goToFirstPage,
    goToLastPage,
    setItemsPerPage,
    setTotalItems,
    getPageNumbers,
    getPaginatedItems
  }
}