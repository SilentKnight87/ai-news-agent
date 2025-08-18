'use client'

import React, { Component, ErrorInfo, ReactNode } from 'react'
import { AlertTriangle, RefreshCw, Wifi, Database, Shield } from 'lucide-react'
import { PostgrestError } from '@supabase/supabase-js'

interface Props {
  children: ReactNode
  fallback?: ReactNode
}

interface State {
  hasError: boolean
  error: Error | null
}

/**
 * Detects if an error is database-related (Supabase PostgrestError).
 */
function isDatabaseError(error: Error): error is PostgrestError {
  return 'code' in error && 'hint' in error && 'details' in error
}

/**
 * Gets user-friendly error message and icon based on error type.
 */
function getErrorInfo(error: Error): { message: string; icon: React.ComponentType<{ className?: string; size?: string | number }>; severity: 'error' | 'warning' | 'info' } {
  if (isDatabaseError(error)) {
    // Supabase/PostgreSQL specific errors
    switch (error.code) {
      case 'PGRST204':
        return {
          message: 'No data found. This might be expected.',
          icon: Database,
          severity: 'info'
        }
      case 'PGRST301':
        return {
          message: 'Database connection failed. Please check your internet connection.',
          icon: Wifi,
          severity: 'error'
        }
      case 'PGRST116':
      case 'PGRST202':
        return {
          message: 'Access denied. You may not have permission to view this content.',
          icon: Shield,
          severity: 'warning'
        }
      case 'PGRST100':
        return {
          message: 'Database query failed. Please try again.',
          icon: Database,
          severity: 'error'
        }
      default:
        return {
          message: `Database error: ${error.message}`,
          icon: Database,
          severity: 'error'
        }
    }
  }

  // Network-related errors
  if (error.message.includes('fetch') || error.message.includes('network') || error.message.includes('Failed to fetch')) {
    return {
      message: 'Connection failed. Please check your internet connection and try again.',
      icon: Wifi,
      severity: 'error'
    }
  }

  // Authentication errors
  if (error.message.includes('auth') || error.message.includes('unauthorized') || error.message.includes('forbidden')) {
    return {
      message: 'Access denied. Please refresh the page and try again.',
      icon: Shield,
      severity: 'warning'
    }
  }

  // Generic error
  return {
    message: error.message || 'An unexpected error occurred',
    icon: AlertTriangle,
    severity: 'error'
  }
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null
  }

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Uncaught error:', error, errorInfo)
    
    // Log additional context for database errors
    if (isDatabaseError(error)) {
      console.error('Database error details:', {
        code: error.code,
        hint: error.hint,
        details: error.details
      })
    }
  }

  private handleReset = () => {
    this.setState({ hasError: false, error: null })
  }

  private handleReload = () => {
    window.location.reload()
  }

  public render() {
    if (this.state.hasError && this.state.error) {
      if (this.props.fallback) {
        return this.props.fallback
      }

      const { message, icon: ErrorIcon, severity } = getErrorInfo(this.state.error)
      
      const severityStyles = {
        error: {
          iconColor: 'text-red-500',
          bgColor: 'bg-red-900/20',
          borderColor: 'border-red-500/30'
        },
        warning: {
          iconColor: 'text-yellow-500',
          bgColor: 'bg-yellow-900/20',
          borderColor: 'border-yellow-500/30'
        },
        info: {
          iconColor: 'text-blue-500',
          bgColor: 'bg-blue-900/20',
          borderColor: 'border-blue-500/30'
        }
      }

      const styles = severityStyles[severity]

      return (
        <div className={`flex flex-col items-center justify-center min-h-[200px] p-6 ${styles.bgColor} border ${styles.borderColor} rounded-lg`}>
          <ErrorIcon className={`w-12 h-12 ${styles.iconColor} mb-4`} />
          <h2 className="text-xl font-semibold text-white mb-2">
            {severity === 'error' ? 'Something went wrong' : 
             severity === 'warning' ? 'Access Issue' : 'Information'}
          </h2>
          <p className="text-gray-400 text-center mb-4 max-w-md">
            {message}
          </p>
          <div className="flex space-x-3">
            <button
              onClick={this.handleReset}
              className="flex items-center space-x-2 px-4 py-2 bg-white text-black rounded-lg hover:bg-gray-200 transition-colors"
            >
              <RefreshCw size={16} />
              <span>Try again</span>
            </button>
            {severity === 'error' && (
              <button
                onClick={this.handleReload}
                className="flex items-center space-x-2 px-4 py-2 bg-gray-700 text-white rounded-lg hover:bg-gray-600 transition-colors"
              >
                <RefreshCw size={16} />
                <span>Reload page</span>
              </button>
            )}
          </div>
          {process.env.NODE_ENV === 'development' && (
            <details className="mt-4 p-3 bg-gray-800 rounded text-xs text-gray-300 max-w-md">
              <summary className="cursor-pointer font-mono">Debug info</summary>
              <pre className="mt-2 whitespace-pre-wrap break-words">
                {JSON.stringify(this.state.error, null, 2)}
              </pre>
            </details>
          )}
        </div>
      )
    }

    return this.props.children
  }
}

// Specific error boundary for article components
export function ArticleErrorBoundary({ children }: { children: ReactNode }) {
  return (
    <ErrorBoundary
      fallback={
        <div className="w-80 h-[420px] bg-gray-900 border border-gray-700 rounded-lg p-4 flex flex-col items-center justify-center">
          <Database className="w-8 h-8 text-gray-600 mb-2" />
          <p className="text-gray-400 text-sm text-center">Failed to load article</p>
          <p className="text-gray-500 text-xs text-center mt-1">Check your connection and try refreshing</p>
        </div>
      }
    >
      {children}
    </ErrorBoundary>
  )
}

// Specific error boundary for digest components
export function DigestErrorBoundary({ children }: { children: ReactNode }) {
  return (
    <ErrorBoundary
      fallback={
        <div className="bg-gray-900 border border-gray-700 rounded-lg p-6 flex flex-col items-center justify-center min-h-[200px]">
          <Database className="w-10 h-10 text-gray-600 mb-3" />
          <p className="text-gray-400 text-sm text-center">Failed to load digest</p>
          <p className="text-gray-500 text-xs text-center mt-1">Database connection issue</p>
        </div>
      }
    >
      {children}
    </ErrorBoundary>
  )
}

// Specific error boundary for search components
export function SearchErrorBoundary({ children }: { children: ReactNode }) {
  return (
    <ErrorBoundary
      fallback={
        <div className="bg-gray-900 border border-gray-700 rounded-lg p-4 flex flex-col items-center justify-center min-h-[100px]">
          <AlertTriangle className="w-6 h-6 text-yellow-500 mb-2" />
          <p className="text-gray-400 text-sm text-center">Search failed</p>
          <p className="text-gray-500 text-xs text-center mt-1">Please try a different search term</p>
        </div>
      }
    >
      {children}
    </ErrorBoundary>
  )
}