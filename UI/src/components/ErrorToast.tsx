'use client'

import React, { useEffect, useState } from 'react'
import { AlertTriangle, X, Wifi, Database, Shield, Info } from 'lucide-react'
import { useErrorDisplay } from '@/hooks/useSupabaseError'

interface ErrorToastProps {
  error: Error | null
  onDismiss?: () => void
  autoHideDuration?: number
  position?: 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left' | 'top-center'
}

/**
 * Toast component for displaying errors with appropriate icons and styling.
 * Automatically hides after a specified duration.
 */
export function ErrorToast({ 
  error, 
  onDismiss, 
  autoHideDuration = 5000,
  position = 'top-right'
}: ErrorToastProps) {
  const [isVisible, setIsVisible] = useState(false)
  const { getDisplayMessage, getErrorSeverity } = useErrorDisplay()

  useEffect(() => {
    if (error) {
      setIsVisible(true)
      if (autoHideDuration > 0) {
        const timer = setTimeout(() => {
          handleDismiss()
        }, autoHideDuration)
        return () => clearTimeout(timer)
      }
    } else {
      setIsVisible(false)
    }
  }, [error, autoHideDuration])

  const handleDismiss = () => {
    setIsVisible(false)
    onDismiss?.()
  }

  if (!error || !isVisible) {
    return null
  }

  const severity = getErrorSeverity(error)
  const message = getDisplayMessage(error)

  const getIcon = () => {
    if (error.message.includes('fetch') || error.message.includes('network')) {
      return Wifi
    }
    if ('code' in error) {
      return Database
    }
    if (error.message.toLowerCase().includes('auth')) {
      return Shield
    }
    if (severity === 'info') {
      return Info
    }
    return AlertTriangle
  }

  const Icon = getIcon()

  const severityStyles = {
    error: {
      bgColor: 'bg-red-900/90',
      borderColor: 'border-red-500',
      iconColor: 'text-red-400',
      textColor: 'text-red-100'
    },
    warning: {
      bgColor: 'bg-yellow-900/90',
      borderColor: 'border-yellow-500',
      iconColor: 'text-yellow-400',
      textColor: 'text-yellow-100'
    },
    info: {
      bgColor: 'bg-blue-900/90',
      borderColor: 'border-blue-500',
      iconColor: 'text-blue-400',
      textColor: 'text-blue-100'
    }
  }

  const styles = severityStyles[severity]

  const positionStyles = {
    'top-right': 'top-4 right-4',
    'top-left': 'top-4 left-4',
    'bottom-right': 'bottom-4 right-4',
    'bottom-left': 'bottom-4 left-4',
    'top-center': 'top-4 left-1/2 -translate-x-1/2'
  }

  return (
    <div className={`fixed ${positionStyles[position]} z-50 animate-in slide-in-from-top-2 duration-300`}>
      <div className={`
        ${styles.bgColor} ${styles.borderColor} ${styles.textColor}
        border backdrop-blur-sm rounded-lg p-4 shadow-lg
        max-w-sm min-w-[300px]
      `}>
        <div className="flex items-start space-x-3">
          <Icon className={`w-5 h-5 ${styles.iconColor} flex-shrink-0 mt-0.5`} />
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium leading-5">
              {message}
            </p>
          </div>
          <button
            onClick={handleDismiss}
            className={`${styles.textColor} hover:${styles.iconColor} transition-colors p-1 -m-1`}
            aria-label="Dismiss error"
          >
            <X size={16} />
          </button>
        </div>
      </div>
    </div>
  )
}

/**
 * Hook for managing error toast state.
 * Use this in components that need to display error toasts.
 */
export function useErrorToast() {
  const [error, setError] = useState<Error | null>(null)

  const showError = (error: Error) => {
    setError(error)
  }

  const hideError = () => {
    setError(null)
  }

  return {
    error,
    showError,
    hideError,
    ErrorToast: (props: Omit<ErrorToastProps, 'error' | 'onDismiss'>) => (
      <ErrorToast error={error} onDismiss={hideError} {...props} />
    )
  }
}

/**
 * Global error toast provider.
 * Add this to your app root to handle global error notifications.
 */
export function ErrorToastProvider({ children }: { children: React.ReactNode }) {
  const [errors, setErrors] = useState<Array<{ id: string; error: Error }>>([])

  // Listen for global errors (you can customize this based on your error handling strategy)
  useEffect(() => {
    const handleError = (event: ErrorEvent) => {
      const error = new Error(event.message)
      addError(error)
    }

    const handleUnhandledRejection = (event: PromiseRejectionEvent) => {
      const error = event.reason instanceof Error ? event.reason : new Error(String(event.reason))
      addError(error)
    }

    window.addEventListener('error', handleError)
    window.addEventListener('unhandledrejection', handleUnhandledRejection)

    return () => {
      window.removeEventListener('error', handleError)
      window.removeEventListener('unhandledrejection', handleUnhandledRejection)
    }
  }, [])

  const addError = (error: Error) => {
    const id = Date.now().toString()
    setErrors(prev => [...prev, { id, error }])
  }

  const removeError = (id: string) => {
    setErrors(prev => prev.filter(e => e.id !== id))
  }

  return (
    <>
      {children}
      {errors.map(({ id, error }, index) => (
        <ErrorToast
          key={id}
          error={error}
          onDismiss={() => removeError(id)}
          position="top-right"
          autoHideDuration={5000}
        />
      ))}
    </>
  )
}