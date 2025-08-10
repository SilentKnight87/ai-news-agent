"use client"

import { useState, useEffect } from "react"
import Link from "next/link"
import { Search, Menu, X, RefreshCw, Settings, ChevronDown } from "lucide-react"
import { cn } from "@/lib/utils"
import { motion, AnimatePresence } from "framer-motion"
import SearchBar from "@/components/SearchBar"

const sources = [
  { id: "all", label: "All", icon: "🌐" },
  { id: "arxiv", label: "ArXiv", icon: "📄" },
  { id: "hackernews", label: "Hacker News", icon: "🔥" },
  { id: "rss", label: "RSS", icon: "📰" },
  { id: "youtube", label: "YouTube", icon: "📺" },
  { id: "huggingface", label: "HuggingFace", icon: "🤗" },
  { id: "reddit", label: "Reddit", icon: "🤖" },
  { id: "github", label: "GitHub", icon: "🐙" },
]

export default function Header() {
  const [isScrolled, setIsScrolled] = useState(false)
  const [selectedSource, setSelectedSource] = useState("all")
  const [isSearchOpen, setIsSearchOpen] = useState(false)
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)
  const [searchQuery, setSearchQuery] = useState("")

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 10)
    }

    window.addEventListener("scroll", handleScroll)
    return () => window.removeEventListener("scroll", handleScroll)
  }, [])

  const handleSourceClick = (sourceId: string) => {
    setSelectedSource(sourceId)
    const element = document.getElementById(`section-${sourceId}`)
    if (element) {
      element.scrollIntoView({ behavior: "smooth", block: "start" })
    }
  }

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    if (searchQuery.trim()) {
      console.log("Searching for:", searchQuery)
    }
  }

  const handleRefresh = () => {
    console.log("Refreshing data...")
  }

  return (
    <header
      className={cn(
        "fixed top-0 left-0 right-0 z-50 transition-all duration-300",
        isScrolled
          ? "bg-gray-900/95 backdrop-blur-xl border-b border-gray-800/50 shadow-2xl"
          : "bg-gradient-to-b from-black via-black/90 to-transparent"
      )}
      data-testid="header"
    >
      <div className="container mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-20">
          {/* Logo and Brand - Origin UI Style */}
          <div className="flex items-center space-x-12">
            <Link href="/" className="group flex items-center">
              <motion.div
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                className="relative"
              >
                {/* Logo with proper spacing */}
                <div className="flex flex-col items-start">
                  <span className="text-3xl font-black tracking-tight bg-gradient-to-r from-white to-gray-400 bg-clip-text text-transparent">
                    AI NEWS
                  </span>
                  <span className="text-[10px] font-semibold text-gray-500 uppercase tracking-[0.3em] -mt-1">
                    AGGREGATOR
                  </span>
                </div>
              </motion.div>
            </Link>

            {/* Desktop Navigation - MVP Blocks Style */}
            <nav className="hidden lg:flex items-center">
              <div className="flex items-center bg-gray-900/50 backdrop-blur-sm rounded-xl p-1 border border-gray-800/50">
                {sources.map((source) => (
                  <motion.button
                    key={source.id}
                    onClick={() => handleSourceClick(source.id)}
                    className={cn(
                      "px-5 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 flex items-center gap-2",
                      selectedSource === source.id
                        ? "text-white bg-gray-800 shadow-lg"
                        : "text-gray-400 hover:text-white hover:bg-gray-800/30"
                    )}
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    data-testid={`source-tab-${source.id}`}
                  >
                    <span className="text-base">{source.icon}</span>
                    <span>{source.label}</span>
                  </motion.button>
                ))}
              </div>
            </nav>
          </div>

          {/* Right Side Actions - Origin UI Pattern */}
          <div className="flex items-center gap-3">
            {/* Search Bar - Animated Expansion */}
            <AnimatePresence>
              {isSearchOpen ? (
                <motion.div
                  initial={{ width: 0, opacity: 0 }}
                  animate={{ width: 320, opacity: 1 }}
                  exit={{ width: 0, opacity: 0 }}
                  transition={{ duration: 0.3, ease: "easeOut" }}
                  className="hidden sm:block"
                >
                  <SearchBar onClose={() => setIsSearchOpen(false)} />
                </motion.div>
              ) : (
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={() => setIsSearchOpen(true)}
                  className="p-2.5 hover:bg-gray-800/50 rounded-xl transition-all duration-200 group"
                  aria-label="Search"
                >
                  <Search className="w-5 h-5 text-gray-400 group-hover:text-white transition-colors" />
                </motion.button>
              )}
            </AnimatePresence>

            {/* Action Buttons Group */}
            <div className="flex items-center gap-2 bg-gray-900/30 backdrop-blur-sm rounded-xl p-1 border border-gray-800/30">
              {/* Refresh Button */}
              <motion.button
                whileHover={{ scale: 1.05, rotate: 180 }}
                whileTap={{ scale: 0.95 }}
                onClick={handleRefresh}
                className="p-2.5 hover:bg-gray-800/50 rounded-lg transition-all duration-200 group"
                aria-label="Refresh"
              >
                <RefreshCw className="w-4 h-4 text-gray-400 group-hover:text-white transition-colors" />
              </motion.button>

              {/* Settings Button */}
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                className="p-2.5 hover:bg-gray-800/50 rounded-lg transition-all duration-200 group"
                aria-label="Settings"
              >
                <Settings className="w-4 h-4 text-gray-400 group-hover:text-white transition-colors" />
              </motion.button>
            </div>

            {/* Mobile Menu Toggle */}
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
              className="lg:hidden p-2.5 hover:bg-gray-800/50 rounded-xl transition-all duration-200"
              aria-label="Menu"
            >
              {isMobileMenuOpen ? (
                <X className="w-5 h-5 text-white" />
              ) : (
                <Menu className="w-5 h-5 text-gray-400" />
              )}
            </motion.button>
          </div>
        </div>

        {/* Mobile Navigation - Slide Down Animation */}
        <AnimatePresence>
          {isMobileMenuOpen && (
            <motion.nav
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: "auto", opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.3, ease: "easeOut" }}
              className="lg:hidden overflow-hidden border-t border-gray-800/50"
            >
              <div className="py-4 space-y-2">
                {sources.map((source) => (
                  <button
                    key={source.id}
                    onClick={() => {
                      handleSourceClick(source.id)
                      setIsMobileMenuOpen(false)
                    }}
                    className={cn(
                      "w-full text-left px-6 py-3 rounded-xl text-sm font-medium transition-all duration-200 flex items-center gap-3",
                      selectedSource === source.id
                        ? "text-white bg-gray-800/50"
                        : "text-gray-400 hover:text-white hover:bg-gray-800/30"
                    )}
                  >
                    <span className="text-base">{source.icon}</span>
                    <span>{source.label}</span>
                  </button>
                ))}
              </div>
            </motion.nav>
          )}
        </AnimatePresence>
      </div>
    </header>
  )
}