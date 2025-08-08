"use client"

import { BarChart3, TrendingUp, Clock, Sparkles, Activity } from "lucide-react"
import { motion, Variants, useReducedMotion } from "framer-motion"
import Aurora from "@/components/Aurora"
import { Digest, Stats } from "@/types"

interface HeroSectionProps {
  digest?: Digest
  stats?: Stats
}

export default function HeroSection({ digest, stats }: HeroSectionProps) {
  const reduce = useReducedMotion()

  const containerVariants: Variants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: reduce ? 0 : 0.1,
        delayChildren: reduce ? 0 : 0.2,
      }
    }
  }

  const itemVariants: Variants = {
    hidden: { opacity: 0, y: reduce ? 0 : 20 },
    visible: {
      opacity: 1,
      y: 0,
      transition: {
        duration: reduce ? 0 : 0.5,
        ease: "easeOut"
      }
    }
  }

  return (
    <section className="relative min-h-[600px] bg-gradient-to-b from-black via-gray-900/50 to-black overflow-hidden pt-28 pb-16">
      {/* MVP Blocks Style Background Pattern */}
      <div className="absolute inset-0">
        <Aurora />
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-gray-900/20 via-transparent to-transparent" />
        <div 
          className="absolute inset-0 opacity-5"
          style={{
            backgroundImage: `url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.1'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")`,
          }}
        />
      </div>

      <motion.div
        variants={containerVariants}
        initial="hidden"
        animate="visible"
        className="relative z-10 container mx-auto px-4 sm:px-6 lg:px-8"
      >
        <div className="max-w-7xl mx-auto">
          {/* Top Section - Welcome Message */}
          <motion.div variants={itemVariants} className="text-center mb-12">
            <div className="inline-flex items-center gap-2 px-4 py-2 bg-gray-800/30 backdrop-blur-sm rounded-full border border-gray-700/50 mb-6">
              <Sparkles className="w-4 h-4 text-yellow-400" />
              <span className="text-sm font-medium text-gray-300">AI-Powered Intelligence Platform</span>
            </div>
            <h1 className="text-5xl lg:text-7xl font-black text-white mb-4 tracking-tight">
              Your Daily
              <span className="bg-gradient-to-r from-white via-gray-300 to-gray-500 bg-clip-text text-transparent"> AI Intelligence</span>
            </h1>
            <p className="text-xl text-gray-400 max-w-3xl mx-auto">
              Stay ahead with curated insights from the world of artificial intelligence. 
              Real-time aggregation from 7+ premium sources.
            </p>
          </motion.div>

          {/* Centered Stats Dashboard - MVP Blocks Style */}
          {stats && (
            <motion.div variants={itemVariants} className="max-w-5xl mx-auto space-y-8">
              {/* Stats Grid - Responsive Layout */}
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 lg:gap-6">
                {/* Total Articles Card */}
                <div className="bg-gray-900/30 backdrop-blur-xl rounded-xl p-6 border border-gray-800/50 group hover:border-gray-700/50 transition-all duration-200">
                  <div className="flex items-start justify-between mb-3">
                    <div className="p-2 bg-gradient-to-br from-blue-500/10 to-cyan-500/10 rounded-lg">
                      <BarChart3 className="w-4 h-4 text-blue-400" />
                    </div>
                  </div>
                  <p className="text-3xl font-black text-white mb-1">
                    {stats?.total_articles?.toLocaleString() || '0'}
                  </p>
                  <p className="text-xs text-gray-500 font-medium uppercase tracking-wider">Total Articles</p>
                </div>

                {/* Average Relevance Card */}
                <div className="bg-gray-900/30 backdrop-blur-xl rounded-xl p-6 border border-gray-800/50 group hover:border-gray-700/50 transition-all duration-200">
                  <div className="flex items-start justify-between mb-3">
                    <div className="p-2 bg-gradient-to-br from-green-500/10 to-emerald-500/10 rounded-lg">
                      <TrendingUp className="w-4 h-4 text-green-400" />
                    </div>
                  </div>
                  <p className="text-3xl font-black text-white mb-1 flex items-baseline">
                    {stats?.avg_relevance_score?.toFixed(1) || '0'}
                    <span className="text-lg font-normal text-gray-400 ml-1">%</span>
                  </p>
                  <p className="text-xs text-gray-500 font-medium uppercase tracking-wider">Avg Relevance</p>
                </div>

                {/* Last 24h Card */}
                <div className="bg-gray-900/30 backdrop-blur-xl rounded-xl p-6 border border-gray-800/50 group hover:border-gray-700/50 transition-all duration-200">
                  <div className="flex items-start justify-between mb-3">
                    <div className="p-2 bg-gradient-to-br from-purple-500/10 to-pink-500/10 rounded-lg">
                      <Clock className="w-4 h-4 text-purple-400" />
                    </div>
                  </div>
                  <p className="text-3xl font-black text-white mb-1">
                    {stats?.articles_last_24h?.toLocaleString() || '0'}
                  </p>
                  <p className="text-xs text-gray-500 font-medium uppercase tracking-wider">Last 24 Hours</p>
                </div>

                {/* Last Week Card */}
                <div className="bg-gray-900/30 backdrop-blur-xl rounded-xl p-6 border border-gray-800/50 group hover:border-gray-700/50 transition-all duration-200">
                  <div className="flex items-start justify-between mb-3">
                    <div className="p-2 bg-gradient-to-br from-orange-500/10 to-red-500/10 rounded-lg">
                      <Activity className="w-4 h-4 text-orange-400" />
                    </div>
                  </div>
                  <p className="text-3xl font-black text-white mb-1">
                    {stats?.articles_last_week?.toLocaleString() || '0'}
                  </p>
                  <p className="text-xs text-gray-500 font-medium uppercase tracking-wider">Last 7 Days</p>
                </div>
              </div>

              {/* Source Distribution - Centered and Wider */}
              <div className="bg-gray-900/30 backdrop-blur-xl rounded-xl p-8 border border-gray-800/50 max-w-3xl mx-auto">
                <h4 className="text-lg font-semibold text-white mb-6 text-center">Source Distribution</h4>
                <div className="space-y-5">
                  {stats?.articles_by_source && Object.entries(stats.articles_by_source)
                    .sort(([, a], [, b]) => b - a)
                    .slice(0, 5)
                    .map(([source, count]) => {
                      const percentage = (count / (stats?.total_articles || 1)) * 100;
                      return (
                        <div key={source} className="group">
                          <div className="flex items-center justify-between mb-3">
                            <span className="text-base font-medium text-gray-300 capitalize group-hover:text-white transition-colors">
                              {source}
                            </span>
                            <div className="flex items-center gap-3">
                              <span className="text-sm text-gray-400 font-semibold">{percentage.toFixed(1)}%</span>
                              <span className="text-sm text-gray-600 font-medium">({count} articles)</span>
                            </div>
                          </div>
                          <div className="relative h-2 bg-gray-800 rounded-full overflow-hidden">
                            <motion.div
                              className="absolute top-0 left-0 h-full bg-gradient-to-r from-gray-600 to-gray-400 rounded-full shadow-sm"
                              initial={{ width: 0 }}
                              animate={{ width: `${percentage}%` }}
                              transition={{ duration: 1, delay: 0.1, ease: "easeOut" }}
                            />
                          </div>
                        </div>
                      );
                    })}
                </div>
              </div>
            </motion.div>
          )}
        </div>
      </motion.div>
    </section>
  )
}