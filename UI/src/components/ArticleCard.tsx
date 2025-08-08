"use client"

import { Article } from "@/types"
import { formatDistanceToNow } from "date-fns"
import { Calendar, TrendingUp, Play, MessageSquare } from "lucide-react"
import { motion, useReducedMotion } from "framer-motion"
import Image from "next/image"
import { cn } from "@/lib/utils"

interface ArticleCardProps {
  article: Article
  onClick: (article: Article) => void
  isVideo?: boolean
}

export default function ArticleCard({ article, onClick, isVideo }: ArticleCardProps) {
  const reduce = useReducedMotion()
  const getRelevanceColor = (score: number) => {
    if (score >= 80) return "from-green-500/20 to-emerald-500/20 border-green-500/30"
    if (score >= 60) return "from-yellow-500/20 to-amber-500/20 border-yellow-500/30"
    return "from-red-500/20 to-rose-500/20 border-red-500/30"
  }

  const getRelevanceTextColor = (score: number) => {
    if (score >= 80) return "text-green-400"
    if (score >= 60) return "text-yellow-400"
    return "text-red-400"
  }

  const getSourceIcon = (source: string) => {
    const icons: Record<string, string> = {
      arxiv: "📄",
      hackernews: "🔥",
      rss: "📰",
      youtube: "📺",
      huggingface: "🤗",
      reddit: "🤖",
      github: "🐙",
    }
    return icons[source.toLowerCase()] || "📄"
  }

  const truncateText = (text: string, maxLength: number) => {
    if (text.length <= maxLength) return text
    return text.substring(0, maxLength).trim() + "..."
  }

  return (
    <motion.article
      className="group relative flex-shrink-0 w-80"
      whileHover={reduce ? undefined : { scale: 1.02 }}
      transition={{ duration: reduce ? 0 : 0.2, ease: "easeOut" }}
    >
      <button
        onClick={() => onClick(article)}
        className="w-full h-full text-left focus:outline-none focus-visible:ring-2 focus-visible:ring-white focus-visible:ring-offset-2 focus-visible:ring-offset-black rounded-xl"
        aria-label={`Read article: ${article.title}`}
      >
        {/* Netflix-style Card with Origin UI Styling */}
        <div className="relative h-[420px] bg-gradient-to-b from-gray-900/50 to-gray-900/80 backdrop-blur-sm rounded-xl border border-gray-800/50 overflow-hidden transition-all duration-300 hover:border-gray-700/50 hover:shadow-2xl">
          {/* Top Section - Image or Gradient */}
          <div className="relative h-44 overflow-hidden bg-gradient-to-br from-gray-800 to-gray-900">
            {article.thumbnail ? (
              <div className="absolute inset-0">
                <Image
                  src={article.thumbnail}
                  alt={article.title}
                  fill
                  className="object-cover transition-transform duration-500 group-hover:scale-105"
                  sizes="(max-width: 768px) 320px, 320px"
                  priority={false}
                />
              </div>
            ) : (
              <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-gray-800/50 to-gray-900/50">
                <div className="text-6xl opacity-20">{getSourceIcon(article.source)}</div>
              </div>
            )}
            
            {/* Overlay Gradient */}
            <div className="absolute inset-0 bg-gradient-to-t from-gray-900 via-gray-900/50 to-transparent" />
            
            {/* Video Indicator */}
            {isVideo && (
              <div className="absolute top-3 right-3 p-2 bg-black/60 backdrop-blur-sm rounded-lg">
                <Play className="w-4 h-4 text-white" />
              </div>
            )}

            {/* Source Badge with subtle gradient border */}
            <div className="absolute top-3 left-3 p-[1px] rounded-lg bg-gradient-to-r from-white/10 to-white/5">
              <div className="flex items-center gap-2 px-3 py-1.5 bg-black/60 backdrop-blur-sm rounded-[7px]">
                <span className="text-sm">{getSourceIcon(article.source)}</span>
                <span className="text-xs font-medium text-gray-200 capitalize">{article.source}</span>
              </div>
            </div>

            {/* Soft glow ring on hover */}
            <div className="absolute inset-0 rounded-xl ring-0 group-hover:ring-2 ring-white/5 transition" />
          </div>

          {/* Content Section with grid to lock bottom row alignment */}
          <div className="relative p-5 grid grid-rows-[auto_auto_auto_1fr_auto] gap-3 h-[244px]">
            {/* Title (reserve space for up to 2 lines) */}
            <h3 className="min-h-[44px] text-base font-semibold text-white leading-snug line-clamp-2 group-hover:text-gray-100 transition-colors">
              {article.title}
            </h3>

            {/* Description (reserve space for up to 2 lines) */}
            <p className="min-h-[48px] text-sm text-gray-400 line-clamp-2 leading-relaxed">
              {truncateText(article.summary || article.content || "", 120)}
            </p>

            {/* Tags -> use categories preview; reserve fixed height to align cards */}
            <div className="pt-2 min-h-[44px]">
              <div className="flex flex-wrap gap-1.5">
                {(article.categories || []).slice(0, 3).map((category: string, index: number) => (
                  <span
                    key={index}
                    className="px-2 py-1 text-[10px] font-medium text-gray-400 bg-gray-800/50 rounded-md uppercase tracking-wider"
                  >
                    {category}
                  </span>
                ))}
              </div>
            </div>

            {/* Spacer row to push footer to bottom consistently */}
            <div />

            {/* Bottom row: date left, relevance right */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-1.5 text-xs text-gray-500">
                <Calendar className="w-3 h-3" />
                <span>{formatDistanceToNow(new Date(article.published_at), { addSuffix: true })}</span>
              </div>

              <div className={cn(
                "px-3 py-1.5 rounded-lg bg-gradient-to-br border",
                getRelevanceColor(article.relevance_score)
              )}>
                <div className="flex items-center gap-1.5">
                  <TrendingUp className="w-3 h-3" />
                  <span className={cn("text-xs font-bold", getRelevanceTextColor(article.relevance_score))}>
                    {article.relevance_score}%
                  </span>
                </div>
              </div>
            </div>

            {/* Comments/Engagement placeholder (kept hidden) */}
            <div className="hidden">
              <MessageSquare className="w-3 h-3" />
            </div>
          </div>

          {/* Hover Effect - Bottom Gradient */}
          <div className="absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r from-gray-700 via-gray-600 to-gray-700 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
        </div>
      </button>
    </motion.article>
  )
}