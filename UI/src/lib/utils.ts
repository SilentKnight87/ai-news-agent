import { type ClassValue, clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatTimeAgo(date: string | Date): string {
  const now = new Date()
  const past = new Date(date)
  const diffInSeconds = Math.floor((now.getTime() - past.getTime()) / 1000)

  if (diffInSeconds < 60) return 'just now'
  if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)}m ago`
  if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)}h ago`
  if (diffInSeconds < 604800) return `${Math.floor(diffInSeconds / 86400)}d ago`
  return past.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}

export function getSourceIcon(source: string): string {
  const icons: Record<string, string> = {
    arxiv: '📄',
    hackernews: '🔥',
    rss: '📰',
    github: '🐙',
    reddit: '🤖',
    twitter: '🐦',
    default: '📊',
  }
  return icons[source.toLowerCase()] || icons.default
}

export function formatDuration(seconds: number): string {
  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = seconds % 60
  return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`
}

export function getRelevanceColor(score: number): string {
  if (score >= 80) return 'from-green-500/20 to-emerald-500/20 border-green-500/30'
  if (score >= 60) return 'from-yellow-500/20 to-amber-500/20 border-yellow-500/30'
  return 'from-red-500/20 to-rose-500/20 border-red-500/30'
}

export function getRelevanceTextColor(score: number): string {
  if (score >= 80) return 'text-green-400'
  if (score >= 60) return 'text-yellow-400'
  return 'text-red-400'
}