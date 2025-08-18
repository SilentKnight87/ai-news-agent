import { useCallback } from 'react'
import { PostgrestError } from '@supabase/supabase-js'

export interface SupabaseErrorInfo {
  message: string
  code?: string
  severity: 'error' | 'warning' | 'info'
  retry: boolean
  details?: string
}

/**
 * Hook for handling and parsing Supabase/PostgreSQL errors.
 * Provides consistent error handling across the application.
 * 
 * Returns:
 *   parseError: Function to parse and format errors for display
 */
export function useSupabaseError() {
  const parseError = useCallback((error: Error | PostgrestError | unknown): SupabaseErrorInfo => {
    if (!error) {
      return {
        message: 'An unknown error occurred',
        severity: 'error',
        retry: true
      }
    }

    // Handle Supabase PostgrestError
    if (typeof error === 'object' && error !== null && 'code' in error && 'message' in error) {
      const postgrestError = error as PostgrestError
      
      switch (postgrestError.code) {
        case 'PGRST204':
          return {
            message: 'No data found',
            code: postgrestError.code,
            severity: 'info',
            retry: false,
            details: 'This query returned no results. This might be expected.'
          }

        case 'PGRST301':
          return {
            message: 'Database connection failed',
            code: postgrestError.code,
            severity: 'error',
            retry: true,
            details: 'Unable to connect to the database. Check your internet connection.'
          }

        case 'PGRST116':
          return {
            message: 'Access denied',
            code: postgrestError.code,
            severity: 'warning',
            retry: false,
            details: 'You do not have permission to access this resource.'
          }

        case 'PGRST202':
          return {
            message: 'Insufficient privileges',
            code: postgrestError.code,
            severity: 'warning',
            retry: false,
            details: 'Row Level Security policy denied access to this data.'
          }

        case 'PGRST100':
          return {
            message: 'Database query failed',
            code: postgrestError.code,
            severity: 'error',
            retry: true,
            details: 'The database query could not be executed successfully.'
          }

        case 'PGRST102':
          return {
            message: 'Invalid request',
            code: postgrestError.code,
            severity: 'error',
            retry: false,
            details: 'The query contains invalid parameters or syntax.'
          }

        case 'PGRST103':
          return {
            message: 'Database constraint violation',
            code: postgrestError.code,
            severity: 'error',
            retry: false,
            details: 'The operation violates a database constraint.'
          }

        default:
          return {
            message: postgrestError.message || 'Database error',
            code: postgrestError.code,
            severity: 'error',
            retry: true,
            details: postgrestError.hint || postgrestError.details
          }
      }
    }

    // Handle standard JavaScript errors
    if (error instanceof Error) {
      // Network connectivity errors
      if (error.message.includes('fetch') || 
          error.message.includes('network') || 
          error.message.includes('Failed to fetch') ||
          error.message.includes('NetworkError')) {
        return {
          message: 'Connection failed',
          severity: 'error',
          retry: true,
          details: 'Network error - check your internet connection and try again.'
        }
      }

      // Authentication/authorization errors
      if (error.message.toLowerCase().includes('auth') ||
          error.message.toLowerCase().includes('unauthorized') ||
          error.message.toLowerCase().includes('forbidden')) {
        return {
          message: 'Access denied',
          severity: 'warning',
          retry: false,
          details: 'Authentication or authorization failed. Please refresh and try again.'
        }
      }

      // Timeout errors
      if (error.message.includes('timeout') || error.message.includes('abort')) {
        return {
          message: 'Request timed out',
          severity: 'error',
          retry: true,
          details: 'The request took too long to complete. Please try again.'
        }
      }

      return {
        message: error.message,
        severity: 'error',
        retry: true,
        details: 'An unexpected error occurred.'
      }
    }

    // Fallback for unknown error types
    return {
      message: String(error),
      severity: 'error',
      retry: true,
      details: 'An unexpected error occurred.'
    }
  }, [])

  return { parseError }
}

/**
 * Hook for displaying user-friendly error messages.
 * Abstracts away technical details while providing helpful guidance.
 */
export function useErrorDisplay() {
  const { parseError } = useSupabaseError()

  const getDisplayMessage = useCallback((error: Error | PostgrestError | unknown): string => {
    const errorInfo = parseError(error)
    
    switch (errorInfo.severity) {
      case 'info':
        return errorInfo.message
      case 'warning':
        return `${errorInfo.message}${errorInfo.retry ? ' Please try again.' : ''}`
      case 'error':
      default:
        return `${errorInfo.message}${errorInfo.retry ? ' Please try again.' : ' Please contact support if this persists.'}`
    }
  }, [parseError])

  const shouldShowRetry = useCallback((error: Error | PostgrestError | unknown): boolean => {
    const errorInfo = parseError(error)
    return errorInfo.retry
  }, [parseError])

  const getErrorSeverity = useCallback((error: Error | PostgrestError | unknown): 'error' | 'warning' | 'info' => {
    const errorInfo = parseError(error)
    return errorInfo.severity
  }, [parseError])

  return {
    getDisplayMessage,
    shouldShowRetry,
    getErrorSeverity,
    parseError
  }
}