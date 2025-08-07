import useSWR from 'swr'
import { api } from '@/lib/api'
import { ArticleFilters } from '@/types'

export function useArticles(source?: string, filters?: ArticleFilters) {
  const key = source 
    ? ['articles', source, filters] 
    : ['articles', filters]
    
  return useSWR(key, () => 
    api.articles.list({ 
      source, 
      ...filters 
    })
  )
}

export function useArticle(id: string) {
  return useSWR(
    id ? ['article', id] : null,
    () => api.articles.get(id)
  )
}

export function useDigest() {
  return useSWR('digest', api.digest.latest, {
    refreshInterval: 60000, // Refresh every minute
  })
}

export function useStats() {
  return useSWR('stats', api.stats, {
    refreshInterval: 30000, // Refresh every 30 seconds
  })
}