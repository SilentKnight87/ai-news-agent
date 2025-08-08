"use client"

import { useState } from "react"
import { Sliders, Clock, TrendingUp, SortAsc, SortDesc, Filter } from "lucide-react"
import { motion, AnimatePresence } from "framer-motion"
import { cn } from "@/lib/utils"

interface FilterBarProps {
  onFilterChange: (filters: FilterState) => void
  className?: string
}

export interface FilterState {
  relevance: number
  timeRange: string
  sortBy: "date" | "relevance"
  order: "asc" | "desc"
}

const timeRanges = [
  { value: "all", label: "All Time" },
  { value: "1h", label: "Last Hour" },
  { value: "24h", label: "Last 24 Hours" },
  { value: "7d", label: "Last 7 Days" },
  { value: "30d", label: "Last 30 Days" },
]

export default function FilterBar({ onFilterChange, className }: FilterBarProps) {
  const [filters, setFilters] = useState<FilterState>({
    relevance: 0,
    timeRange: "all",
    sortBy: "date",
    order: "desc",
  })
  const [showAdvanced, setShowAdvanced] = useState(false)

  const updateFilter = <K extends keyof FilterState>(key: K, value: FilterState[K]) => {
    const newFilters = { ...filters, [key]: value }
    setFilters(newFilters)
    onFilterChange(newFilters)
  }

  const resetFilters = () => {
    const defaultFilters: FilterState = {
      relevance: 0,
      timeRange: "all",
      sortBy: "date",
      order: "desc",
    }
    setFilters(defaultFilters)
    onFilterChange(defaultFilters)
  }

  return (
    <div className={cn("bg-gray-900/50 backdrop-blur-sm border-y border-gray-800", className)}>
      <div className="px-4 sm:px-6 lg:px-8 py-4">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between space-y-4 lg:space-y-0">
          {/* Primary Filters */}
          <div className="flex flex-wrap items-center gap-4">
            {/* Relevance Slider */}
            <div className="flex items-center gap-3">
              <div className="flex items-center space-x-2">
                <TrendingUp className="w-4 h-4 text-gray-400" />
                <span className="text-sm text-gray-300">Relevance</span>
              </div>
              <div className="flex items-center gap-2 w-48 sm:w-56">
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={filters.relevance}
                  onChange={(e) => updateFilter("relevance", parseInt(e.target.value))}
                  className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer slider"
                  style={{
                    background: `linear-gradient(to right, #10b981 0%, #10b981 ${filters.relevance}%, #374151 ${filters.relevance}%, #374151 100%)`
                  }}
                />
                <span className="text-xs text-gray-400 tabular-nums w-10 text-right">
                  {filters.relevance}%
                </span>
              </div>
            </div>

            {/* Time Range Dropdown */}
            <div className="flex items-center space-x-2 min-w-36">
              <Clock className="w-4 h-4 text-gray-400" />
              <select
                value={filters.timeRange}
                onChange={(e) => updateFilter("timeRange", e.target.value)}
                className="bg-gray-800 text-gray-300 text-sm rounded-lg px-3 py-1.5 border border-gray-700 focus:outline-none focus:border-gray-500 transition-colors"
              >
                {timeRanges.map((range) => (
                  <option key={range.value} value={range.value}>
                    {range.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Sort Options */}
            <div className="flex items-center space-x-2 min-w-28">
              <Filter className="w-4 h-4 text-gray-400" />
              <select
                value={filters.sortBy}
                onChange={(e) => updateFilter("sortBy", e.target.value as "date" | "relevance")}
                className="bg-gray-800 text-gray-300 text-sm rounded-lg px-3 py-1.5 border border-gray-700 focus:outline-none focus:border-gray-500 transition-colors"
              >
                <option value="date">Date</option>
                <option value="relevance">Relevance</option>
              </select>
            </div>

            {/* Order Toggle */}
            <button
              onClick={() => updateFilter("order", filters.order === "asc" ? "desc" : "asc")}
              className="p-2 bg-gray-800 hover:bg-gray-700 rounded-lg transition-colors"
              aria-label={`Sort ${filters.order === "asc" ? "ascending" : "descending"}`}
            >
              {filters.order === "asc" ? (
                <SortAsc className="w-4 h-4 text-gray-400" />
              ) : (
                <SortDesc className="w-4 h-4 text-gray-400" />
              )}
            </button>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center space-x-3">
            <button
              onClick={() => setShowAdvanced(!showAdvanced)}
              className="flex items-center space-x-2 px-4 py-2 text-sm text-gray-300 hover:text-white transition-colors"
            >
              <Sliders className="w-4 h-4" />
              <span>Advanced</span>
            </button>
            <button
              onClick={resetFilters}
              className="px-4 py-2 text-sm text-gray-400 hover:text-white transition-colors"
            >
              Reset
            </button>
          </div>
        </div>

        {/* Advanced Filters */}
        <AnimatePresence>
          {showAdvanced && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: "auto", opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.3 }}
              className="mt-4 pt-4 border-t border-gray-800 overflow-hidden"
            >
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                {/* Category Filter */}
                <div>
                  <label className="block text-sm text-gray-400 mb-2">Category</label>
                  <select className="w-full bg-gray-800 text-gray-300 text-sm rounded-lg px-3 py-2 border border-gray-700 focus:outline-none focus:border-gray-500 transition-colors">
                    <option value="">All Categories</option>
                    <option value="machine-learning">Machine Learning</option>
                    <option value="nlp">Natural Language Processing</option>
                    <option value="computer-vision">Computer Vision</option>
                    <option value="robotics">Robotics</option>
                  </select>
                </div>

                {/* Author Filter */}
                <div>
                  <label className="block text-sm text-gray-400 mb-2">Author</label>
                  <input
                    type="text"
                    placeholder="Filter by author..."
                    className="w-full bg-gray-800 text-gray-300 text-sm rounded-lg px-3 py-2 border border-gray-700 focus:outline-none focus:border-gray-500 transition-colors placeholder-gray-500"
                  />
                </div>

                {/* Min Articles */}
                <div>
                  <label className="block text-sm text-gray-400 mb-2">Min Articles</label>
                  <input
                    type="number"
                    placeholder="0"
                    min="0"
                    className="w-full bg-gray-800 text-gray-300 text-sm rounded-lg px-3 py-2 border border-gray-700 focus:outline-none focus:border-gray-500 transition-colors placeholder-gray-500"
                  />
                </div>

                {/* Keywords */}
                <div>
                  <label className="block text-sm text-gray-400 mb-2">Keywords</label>
                  <input
                    type="text"
                    placeholder="Enter keywords..."
                    className="w-full bg-gray-800 text-gray-300 text-sm rounded-lg px-3 py-2 border border-gray-700 focus:outline-none focus:border-gray-500 transition-colors placeholder-gray-500"
                  />
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Custom slider styles */}
      <style jsx>{`
        .slider::-webkit-slider-thumb {
          appearance: none;
          width: 16px;
          height: 16px;
          background: white;
          border-radius: 50%;
          cursor: pointer;
          transition: all 0.2s;
        }
        
        .slider::-webkit-slider-thumb:hover {
          transform: scale(1.2);
          box-shadow: 0 0 0 8px rgba(255, 255, 255, 0.1);
        }
        
        .slider::-moz-range-thumb {
          width: 16px;
          height: 16px;
          background: white;
          border-radius: 50%;
          cursor: pointer;
          transition: all 0.2s;
          border: none;
        }
        
        .slider::-moz-range-thumb:hover {
          transform: scale(1.2);
          box-shadow: 0 0 0 8px rgba(255, 255, 255, 0.1);
        }
      `}</style>
    </div>
  )
}