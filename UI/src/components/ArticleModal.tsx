"use client"

import { useEffect, useState, useRef } from "react"
import { X, ExternalLink, RefreshCw, Share2, Bookmark, TrendingUp, Clock, User } from "lucide-react"
import { motion, AnimatePresence, useReducedMotion } from "framer-motion"
import { Article } from "@/types"
import { cn, formatTimeAgo, getRelevanceColor, getSourceIcon } from "@/lib/utils"

interface ArticleModalProps {
  article: Article | null
  isOpen: boolean
  onClose: () => void
  onReanalyze?: (id: string) => void
}

export default function ArticleModal({ article, isOpen, onClose, onReanalyze }: ArticleModalProps) {
  const reduce = useReducedMotion()
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [activeTab, setActiveTab] = useState<"summary" | "analysis" | "related">("summary")
  const modalRef = useRef<HTMLDivElement>(null)
  const previousFocusRef = useRef<HTMLElement | null>(null)

  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onClose()
      }
    }

    if (isOpen) {
      // Store current focus
      previousFocusRef.current = document.activeElement as HTMLElement
      
      // Add event listener
      document.addEventListener("keydown", handleEscape)
      document.body.style.overflow = "hidden"
      
      // Focus first focusable element in modal
      setTimeout(() => {
        const firstFocusable = modalRef.current?.querySelector<HTMLElement>(
          'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        )
        firstFocusable?.focus()
      }, 100)
    }

    return () => {
      document.removeEventListener("keydown", handleEscape)
      document.body.style.overflow = "unset"
      
      // Restore previous focus
      if (previousFocusRef.current) {
        previousFocusRef.current.focus()
      }
    }
  }, [isOpen, onClose])

  if (!article) return null

  const handleReanalyze = async () => {
    if (!onReanalyze) return
    setIsAnalyzing(true)
    await onReanalyze(article.id)
    setIsAnalyzing(false)
  }

  const handleShare = async () => {
    if (navigator.share) {
      try {
        await navigator.share({
          title: article.title,
          text: article.summary,
          url: article.url,
        })
      } catch (err) {
        console.log("Error sharing:", err)
      }
    } else {
      // Fallback: Copy to clipboard
      navigator.clipboard.writeText(article.url)
    }
  }

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/80 backdrop-blur-sm z-40"
            onClick={onClose}
            data-testid="modal-backdrop"
          />

          {/* Modal */}
          <motion.div
            ref={modalRef}
            initial={reduce ? { opacity: 0 } : { opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={reduce ? { opacity: 0 } : { opacity: 0, scale: 0.95, y: 20 }}
            transition={{ duration: reduce ? 0 : 0.3, ease: "easeOut" }}
            className="fixed inset-x-4 top-[5%] bottom-[5%] max-w-4xl mx-auto z-50 flex flex-col"
            data-testid="article-modal"
          >
            <div className="bg-gray-900 rounded-xl shadow-2xl flex flex-col h-full overflow-hidden">
              {/* Header */}
              <div className="flex-shrink-0 px-6 py-5 border-b border-gray-800">
                <div className="flex items-start justify-between">
                  <div className="flex-1 pr-4">
                    <h2 className="text-2xl font-bold text-white line-clamp-2">
                      {article.title}
                    </h2>
                    <div className="flex items-center space-x-4 mt-2 text-sm text-gray-400">
                      <span className="flex items-center">
                        <span className="mr-1">{getSourceIcon(article.source)}</span>
                        {article.source}
                      </span>
                      <span className="flex items-center">
                        <Clock className="w-4 h-4 mr-1" />
                        {formatTimeAgo(article.published_at)}
                      </span>
                      <span className={cn("flex items-center font-medium", getRelevanceColor(article.relevance_score))}>
                        <TrendingUp className="w-4 h-4 mr-1" />
                        {article.relevance_score}%
                      </span>
                      {article.author && (
                        <span className="flex items-center">
                          <User className="w-4 h-4 mr-1" />
                          {article.author}
                        </span>
                      )}
                    </div>
                  </div>
                  <button
                    onClick={onClose}
                    className="p-2 hover:bg-gray-800 rounded-lg transition-colors"
                    aria-label="Close modal"
                  >
                    <X className="w-5 h-5 text-gray-400 hover:text-white" />
                  </button>
                </div>

                {/* Categories */}
                {article.categories && article.categories.length > 0 && (
                  <div className="flex flex-wrap gap-2 mt-3">
                    {article.categories.map((category, index) => (
                      <span
                        key={index}
                        className="px-3 py-1 bg-gray-800 text-gray-300 text-xs rounded-full"
                      >
                        {category}
                      </span>
                    ))}
                  </div>
                )}
              </div>

              {/* Tabs */}
              <div className="flex-shrink-0 px-6 border-b border-gray-800">
                <div className="flex space-x-6">
                  {["summary", "analysis", "related"].map((tab) => (
                    <button
                      key={tab}
                      onClick={() => setActiveTab(tab as "summary" | "analysis" | "related")}
                      className={cn(
                        "py-3 text-sm font-medium capitalize border-b-2 transition-colors",
                        activeTab === tab
                          ? "text-white border-white"
                          : "text-gray-400 border-transparent hover:text-gray-200"
                      )}
                    >
                      {tab}
                    </button>
                  ))}
                </div>
              </div>

              {/* Content */}
              <div className="flex-1 overflow-y-auto px-6 py-6">
                <AnimatePresence mode="wait">
                  {activeTab === "summary" && (
                    <motion.div
                      key="summary"
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, x: 20 }}
                      className="space-y-6"
                    >
                      {/* AI Summary */}
                      <div className="bg-gray-800 rounded-lg p-4">
                        <h3 className="text-lg font-semibold text-white mb-3">AI Summary</h3>
                        <p className="text-gray-300 leading-relaxed">
                          {article.summary}
                        </p>
                      </div>

                      {/* Key Points */}
                      <div>
                        <h3 className="text-lg font-semibold text-white mb-3">Key Points</h3>
                        <ul className="space-y-2">
                          <li className="flex items-start">
                            <span className="text-green-400 mr-2 mt-1">•</span>
                            <span className="text-gray-300">Revolutionary AI model achieves 95% accuracy in complex reasoning tasks</span>
                          </li>
                          <li className="flex items-start">
                            <span className="text-green-400 mr-2 mt-1">•</span>
                            <span className="text-gray-300">New architecture reduces computational requirements by 40%</span>
                          </li>
                          <li className="flex items-start">
                            <span className="text-green-400 mr-2 mt-1">•</span>
                            <span className="text-gray-300">Open-source implementation available on GitHub</span>
                          </li>
                        </ul>
                      </div>

                      {/* Full Content */}
                      {article.content && (
                        <div>
                          <h3 className="text-lg font-semibold text-white mb-3">Full Article</h3>
                          <div className="prose prose-invert max-w-none">
                            <p className="text-gray-300 leading-relaxed whitespace-pre-wrap">
                              {article.content}
                            </p>
                          </div>
                        </div>
                      )}
                    </motion.div>
                  )}

                  {activeTab === "analysis" && (
                    <motion.div
                      key="analysis"
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, x: 20 }}
                      className="space-y-6"
                    >
                      <div className="bg-gray-800 rounded-lg p-4">
                        <h3 className="text-lg font-semibold text-white mb-3">AI Analysis</h3>
                        <div className="space-y-4 text-gray-300">
                          <div>
                            <h4 className="font-medium text-white mb-2">Impact Assessment</h4>
                            <p>This development represents a significant breakthrough in AI research, potentially accelerating progress in natural language understanding and reasoning capabilities.</p>
                          </div>
                          <div>
                            <h4 className="font-medium text-white mb-2">Technical Innovation</h4>
                            <p>The novel architecture introduces a hybrid approach combining transformer models with symbolic reasoning, addressing long-standing limitations in current AI systems.</p>
                          </div>
                          <div>
                            <h4 className="font-medium text-white mb-2">Industry Implications</h4>
                            <p>Early adoption could provide competitive advantages in sectors requiring complex decision-making, including healthcare, finance, and autonomous systems.</p>
                          </div>
                        </div>
                      </div>
                    </motion.div>
                  )}

                  {activeTab === "related" && (
                    <motion.div
                      key="related"
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, x: 20 }}
                      className="space-y-4"
                    >
                      <h3 className="text-lg font-semibold text-white mb-3">Related Articles</h3>
                      <div className="grid gap-4">
                        {[1, 2, 3].map((i) => (
                          <div key={i} className="bg-gray-800 rounded-lg p-4 hover:bg-gray-700 transition-colors cursor-pointer">
                            <h4 className="font-medium text-white mb-2">Related Article Title {i}</h4>
                            <p className="text-sm text-gray-400 line-clamp-2">
                              Brief summary of the related article content goes here...
                            </p>
                            <div className="flex items-center space-x-3 mt-2 text-xs text-gray-500">
                              <span>ArXiv</span>
                              <span>2 hours ago</span>
                              <span className="text-green-400">85% relevant</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>

              {/* Footer Actions */}
              <div className="flex-shrink-0 px-6 py-4 border-t border-gray-800">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={handleShare}
                      className="p-2 hover:bg-gray-800 rounded-lg transition-colors"
                      aria-label="Share"
                    >
                      <Share2 className="w-5 h-5 text-gray-400 hover:text-white" />
                    </button>
                    <button
                      className="p-2 hover:bg-gray-800 rounded-lg transition-colors"
                      aria-label="Bookmark"
                    >
                      <Bookmark className="w-5 h-5 text-gray-400 hover:text-white" />
                    </button>
                    {onReanalyze && (
                      <button
                        onClick={handleReanalyze}
                        disabled={isAnalyzing}
                        className="flex items-center space-x-2 px-4 py-2 hover:bg-gray-800 rounded-lg transition-colors disabled:opacity-50"
                      >
                        <RefreshCw className={cn("w-4 h-4 text-gray-400", isAnalyzing && "animate-spin")} />
                        <span className="text-sm text-gray-400">Re-analyze</span>
                      </button>
                    )}
                  </div>
                  <a
                    href={article.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center space-x-2 px-6 py-2 bg-white text-black rounded-lg hover:bg-gray-200 transition-colors font-medium"
                  >
                    <span>View Original</span>
                    <ExternalLink className="w-4 h-4" />
                  </a>
                </div>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  )
}