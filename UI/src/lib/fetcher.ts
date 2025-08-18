/**
 * SWR fetcher function for data fetching with error handling.
 * Used as the default fetcher for all SWR hooks in the application.
 * 
 * Args:
 *   url: URL to fetch data from
 * 
 * Returns:
 *   Promise: Resolved JSON data or thrown error
 */
export const fetcher = async (url: string) => {
  const response = await fetch(url)
  
  if (!response.ok) {
    const error = new Error(`HTTP error! status: ${response.status}`)
    // Attach response status for error handling
    ;(error as Error & { status: number }).status = response.status
    throw error
  }
  
  const data = await response.json()
  return data
}

/**
 * Fetcher function with authentication header.
 * Used for API calls that require authentication.
 * 
 * Args:
 *   url: URL to fetch data from
 *   token: Authentication token
 * 
 * Returns:
 *   Promise: Resolved JSON data or thrown error
 */
export const authenticatedFetcher = async (url: string, token?: string) => {
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
  }
  
  if (token) {
    headers.Authorization = `Bearer ${token}`
  }
  
  const response = await fetch(url, {
    headers,
  })
  
  if (!response.ok) {
    const error = new Error(`HTTP error! status: ${response.status}`)
    ;(error as Error & { status: number }).status = response.status
    throw error
  }
  
  const data = await response.json()
  return data
}

/**
 * POST fetcher function for mutations.
 * 
 * Args:
 *   url: URL to send POST request to
 *   data: Data to send in request body
 * 
 * Returns:
 *   Promise: Resolved JSON data or thrown error
 */
export const postFetcher = async (url: string, data: unknown) => {
  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  })
  
  if (!response.ok) {
    const error = new Error(`HTTP error! status: ${response.status}`)
    ;(error as Error & { status: number }).status = response.status
    throw error
  }
  
  const result = await response.json()
  return result
}

/**
 * Default export for convenience.
 */
export default fetcher