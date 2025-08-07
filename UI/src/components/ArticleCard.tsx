"use client"

import { Article } from "@/types"
import { formatDistanceToNow } from "date-fns"
import { Calendar, Clock, TrendingUp, ExternalLink, Play, FileText, MessageSquare } from "lucide-react"
import { motion } from "framer-motion"
import { cn } from "@/lib/utils"

interface ArticleCardProps {
  article: Article
  onClick: (article: Article) => void
  isVideo?: boolean
}

export default function ArticleCard({ article, onClick, isVideo }: ArticleCardProps) {
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
      whileHover={{ scale: 1.02 }}
      transition={{ duration: 0.2, ease: "easeOut" }}
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
            {article.image_url ? (
              <img
                src={article.image_url}
                alt={article.title}
                className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110"
                loading="lazy"
              />
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

            {/* Source Badge */}
            <div className="absolute top-3 left-3 flex items-center gap-2 px-3 py-1.5 bg-black/60 backdrop-blur-sm rounded-lg">
              <span className="text-sm">{getSourceIcon(article.source)}</span>
              <span className="text-xs font-medium text-gray-200 capitalize">{article.source}</span>
            </div>
          </div>

          {/* Content Section */}
          <div className="relative p-5 space-y-3">
            {/* Title */}
            <h3 className="text-base font-semibold text-white leading-tight line-clamp-2 group-hover:text-gray-100 transition-colors">
              {article.title}
            </h3>

            {/* Description */}
            <p className="text-sm text-gray-400 line-clamp-2 leading-relaxed">
              {truncateText(article.summary || article.content || "", 120)}
            </p>

            {/* Metadata Grid */}
            <div className="flex items-center justify-between pt-2">
              {/* Date */}
              <div className="flex items-center gap-1.5 text-xs text-gray-500">
                <Calendar className="w-3 h-3" />
                <span>{formatDistanceToNow(new Date(article.published_at), { addSuffix: true })}</span>
              </div>

              {/* Comments/Engagement */}
              {article.comments_count !== undefined && article.comments_count > 0 && (
                <div className="flex items-center gap-1.5 text-xs text-gray-500">
                  <MessageSquare className="w-3 h-3" />
                  <span>{article.comments_count}</span>
                </div>
              )}
            </div>

            {/* Relevance Score - Origin UI Style */}
            <div className={cn(
              "absolute bottom-5 right-5 px-3 py-1.5 rounded-lg bg-gradient-to-br border",
              getRelevanceColor(article.relevance_score)
            )}>
              <div className="flex items-center gap-1.5">
                <TrendingUp className="w-3 h-3" />
                <span className={cn("text-xs font-bold", getRelevanceTextColor(article.relevance_score))}>
                  {article.relevance_score}%
                </span>
              </div>
            </div>

            {/* Tags */}
            {article.tags && article.tags.length > 0 && (
              <div className="flex flex-wrap gap-1.5 pt-2">
                {article.tags.slice(0, 3).map((tag, index) => (
                  <span
                    key={index}
                    className="px-2 py-1 text-[10px] font-medium text-gray-400 bg-gray-800/50 rounded-md uppercase tracking-wider"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            )}
          </div>

          {/* Hover Effect - Bottom Gradient */}
          <div className="absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r from-gray-700 via-gray-600 to-gray-700 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
        </div>
      </button>
    </motion.article>
  )
}