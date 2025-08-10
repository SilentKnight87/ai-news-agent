"use client"

import { useState, useEffect } from "react"
import { useSearchParams, useRouter } from "next/navigation"
import { Search, Loader2, AlertCircle, Clock, Filter } from "lucide-react"
import { motion, AnimatePresence } from "framer-motion"
import ArticleCard from "@/components/ArticleCard"
import ArticleModal from "@/components/ArticleModal"
import Pagination from "@/components/Pagination"
import { useDebounce } from "@/hooks/useDebounce"
import { useSearch } from "@/hooks/useSearch"
import { Article } from "@/types"
import { cn } from "@/lib/utils"

const ITEMS_PER_PAGE = 20

const SOURCE_OPTIONS = [
  { id: "all", label: "All Sources" },
  { id: "arxiv", label: "ArXiv" },
  { id: "hackernews", label: "Hacker News" },
  { id: "rss", label: "RSS" },
  { id: "youtube", label: "YouTube" },
  { id: "huggingface", label: "HuggingFace" },
  { id: "reddit", label: "Reddit" },
  { id: "github", label: "GitHub" },
]

export default function SearchPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  
  // State management
  const [query, setQuery] = useState(searchParams.get("q") || "")
  const [source, setSource] = useState(searchParams.get("source") || "all")
  const [currentPage, setCurrentPage] = useState(
    parseInt(searchParams.get("page") || "1", 10)
  )
  const [selectedArticle, setSelectedArticle] = useState<Article | null>(null)
  
  // Debounce search query
  const debouncedQuery = useDebounce(query, 300)
  
  // Calculate offset for pagination
  const offset = (currentPage - 1) * ITEMS_PER_PAGE
  
  // Fetch search results
  const effectiveSource = source === "all" ? undefined : source
  const { data, isLoading, error } = useSearch(
    debouncedQuery,
    effectiveSource,
    ITEMS_PER_PAGE,
    offset
  )
  
  // Update URL params when search criteria changes
  useEffect(() => {
    const params = new URLSearchParams()
    if (debouncedQuery) params.set("q", debouncedQuery)
    if (source !== "all") params.set("source", source)
    if (currentPage > 1) params.set("page", String(currentPage))
    
    const newUrl = params.toString() ? `?${params.toString()}` : "/search"
    router.replace(newUrl, { scroll: false })
  }, [debouncedQuery, source, currentPage, router])
  
  // Reset page when search criteria changes
  useEffect(() => {
    setCurrentPage(1)
  }, [debouncedQuery, source])
  
  // Calculate total pages
  const totalPages = data ? Math.ceil(data.total / ITEMS_PER_PAGE) : 0
  
  const handlePageChange = (page: number) => {
    setCurrentPage(page)
    window.scrollTo({ top: 0, behavior: "smooth" })
  }
  
  const handleClearSearch = () => {
    setQuery("")
    setSource("all")
    setCurrentPage(1)
  }

  return (
    <div className="min-h-screen bg-black pt-20">
      {/* Persistent Search Bar */}
      <div className="sticky top-16 z-40 bg-black/95 backdrop-blur-md border-b border-gray-800">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="max-w-4xl mx-auto">
            <div className="flex flex-col sm:flex-row gap-4">
              {/* Search Input */}
              <div className="relative flex-1">
                <input
                  type="text"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="Search AI news and articles..."
                  className="w-full h-12 pl-12 pr-10 bg-gray-900/80 backdrop-blur-sm border border-gray-700 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:border-gray-500 focus:bg-gray-900 transition-all"
                  autoFocus
                />
                <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-500" />
                {query && (
                  <button
                    onClick={handleClearSearch}
                    className="absolute right-3 top-1/2 -translate-y-1/2 p-1.5 hover:bg-gray-800 rounded-lg transition-colors"
                    aria-label="Clear search"
                  >
                    <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                )}
              </div>
              
              {/* Source Filter */}
              <select
                value={source}
                onChange={(e) => setSource(e.target.value)}
                className="h-12 px-4 bg-gray-900/80 border border-gray-700 rounded-xl text-white focus:outline-none focus:border-gray-500 transition-all"
                aria-label="Filter by source"
              >
                {SOURCE_OPTIONS.map((option) => (
                  <option key={option.id} value={option.id}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>
            
            {/* Search Stats */}
            {data && debouncedQuery && (
              <div className="mt-3 flex items-center gap-4 text-sm text-gray-400">
                <span>{data.total.toLocaleString()} results</span>
                <span className="flex items-center gap-1">
                  <Clock className="w-3.5 h-3.5" />
                  {data.took_ms}ms
                </span>
              </div>
            )}
          </div>
        </div>
      </div>
      
      {/* Main Content */}
      <main className="container mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="max-w-7xl mx-auto">
          {/* Loading State */}
          {isLoading && (
            <div className="flex flex-col items-center justify-center py-20">
              <Loader2 className="w-8 h-8 text-gray-400 animate-spin mb-4" />
              <p className="text-gray-500">Searching...</p>
            </div>
          )}
          
          {/* Error State */}
          {error && !isLoading && (
            <div className="flex flex-col items-center justify-center py-20">
              <AlertCircle className="w-12 h-12 text-red-500 mb-4" />
              <h3 className="text-xl font-semibold text-white mb-2">Search Error</h3>
              <p className="text-gray-400 text-center max-w-md">
                An error occurred while searching. Please try again later.
              </p>
            </div>
          )}
          
          {/* Empty State */}
          {!isLoading && !error && data?.articles?.length === 0 && (
            <div className="flex flex-col items-center justify-center py-20">
              <div className="w-20 h-20 bg-gray-800 rounded-full flex items-center justify-center mb-6">
                <Search className="w-10 h-10 text-gray-600" />
              </div>
              <h3 className="text-xl font-semibold text-white mb-2">No results found</h3>
              <p className="text-gray-400 text-center max-w-md mb-6">
                {debouncedQuery
                  ? `No articles found for "${debouncedQuery}"`
                  : "Enter a search query to find AI news and articles"}
              </p>
              {debouncedQuery && (
                <button
                  onClick={handleClearSearch}
                  className="px-4 py-2 bg-gray-800 hover:bg-gray-700 text-white rounded-lg transition-colors"
                >
                  Clear search
                </button>
              )}
            </div>
          )}
          
          {/* Search Results Grid */}
          {!isLoading && !error && data?.articles && data.articles.length > 0 && (
            <>
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 0.5 }}
                className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6"
              >
                <AnimatePresence mode="popLayout">
                  {data.articles.map((article, index) => (
                    <motion.div
                      key={article.id}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, scale: 0.95 }}
                      transition={{ 
                        duration: 0.3,
                        delay: index * 0.05,
                        ease: "easeOut"
                      }}
                      className="w-full"
                    >
                      <ArticleCard
                        article={article}
                        onClick={setSelectedArticle}
                        isVideo={article.source === "youtube"}
                      />
                    </motion.div>
                  ))}
                </AnimatePresence>
              </motion.div>
              
              {/* Pagination */}
              {totalPages > 1 && (
                <div className="mt-12 flex justify-center">
                  <Pagination
                    currentPage={currentPage}
                    totalPages={totalPages}
                    onPageChange={handlePageChange}
                  />
                </div>
              )}
            </>
          )}
        </div>
      </main>
      
      {/* Article Modal */}
      <ArticleModal
        article={selectedArticle}
        isOpen={!!selectedArticle}
        onClose={() => setSelectedArticle(null)}
      />
    </div>
  )
}