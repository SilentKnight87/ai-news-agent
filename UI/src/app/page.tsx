"use client"

import { useState } from "react"
import HeroSection from "@/components/HeroSection"
import FilterBar, { FilterState } from "@/components/FilterBar"
import ContentRow from "@/components/ContentRow"
import ArticleCard from "@/components/ArticleCard"
import ArticleModal from "@/components/ArticleModal"
import { SkeletonRow } from "@/components/Skeleton"
import { useArticles, useDigest, useStats } from "@/hooks/useArticles"
import { Article } from "@/types"
import { api } from "@/lib/api"

const sources = [
  { id: "arxiv", label: "ArXiv Research Papers", subtitle: "Latest AI research from ArXiv" },
  { id: "hackernews", label: "Hacker News Discussions", subtitle: "Top AI discussions from HN" },
  { id: "rss", label: "RSS News Articles", subtitle: "Curated news from RSS feeds" },
  { id: "youtube", label: "YouTube AI Videos", subtitle: "Educational AI content" },
  { id: "huggingface", label: "HuggingFace Models", subtitle: "Latest models and datasets" },
  { id: "reddit", label: "Reddit Discussions", subtitle: "Community AI discussions" },
  { id: "github", label: "GitHub Tool Updates", subtitle: "Open source AI projects" },
]

export default function Home() {
  const [selectedArticle, setSelectedArticle] = useState<Article | null>(null)
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [filters, setFilters] = useState<FilterState>({
    relevance: 0,
    timeRange: "all",
    sortBy: "date",
    order: "desc",
  })
  const [searchResults] = useState<Article[]>([])
  const [isSearching] = useState(false)

  // Fetch data
  const { data: digestData } = useDigest()
  const { data: statsData } = useStats()

  // Fetch articles for each source
  const arxivArticles = useArticles("arxiv", { relevance_min: filters.relevance })
  const hnArticles = useArticles("hackernews", { relevance_min: filters.relevance })
  const rssArticles = useArticles("rss", { relevance_min: filters.relevance })
  const youtubeArticles = useArticles("youtube", { relevance_min: filters.relevance })
  const huggingfaceArticles = useArticles("huggingface", { relevance_min: filters.relevance })
  const redditArticles = useArticles("reddit", { relevance_min: filters.relevance })
  const githubArticles = useArticles("github", { relevance_min: filters.relevance })

  const sourceData = {
    arxiv: arxivArticles,
    hackernews: hnArticles,
    rss: rssArticles,
    youtube: youtubeArticles,
    huggingface: huggingfaceArticles,
    reddit: redditArticles,
    github: githubArticles,
  }

  const handleArticleClick = (article: Article) => {
    setSelectedArticle(article)
    setIsModalOpen(true)
  }

  const handleCloseModal = () => {
    setIsModalOpen(false)
    setTimeout(() => setSelectedArticle(null), 300)
  }

  const handleRefresh = () => {
    // Refresh all data
    Object.values(sourceData).forEach(source => source?.mutate?.())
  }

  const handleFilterChange = (newFilters: FilterState) => {
    setFilters(newFilters)
  }

  return (
    <div className="min-h-screen bg-black">
      {/* Hero Section */}
      <HeroSection 
        digest={digestData} 
        stats={statsData}
      />

      {/* Filter Bar */}
      <FilterBar 
        onFilterChange={handleFilterChange}
        className="sticky top-20 z-30 bg-black/95 backdrop-blur-xl border-b border-gray-900/50"
      />

      {/* Content Sections */}
      <div className="py-12 space-y-8 bg-black">
        {/* Search Results (if searching) */}
        {isSearching && searchResults.length > 0 && (
          <ContentRow 
            title="Search Results" 
            subtitle={`Found ${searchResults.length} matching articles`}
          >
            {searchResults.map((article) => (
              <ArticleCard
                key={article.id}
                article={article}
                onClick={() => handleArticleClick(article)}
              />
            ))}
          </ContentRow>
        )}

        {/* Daily AI Digests */}
        {digestData && digestData.articles && digestData.articles.length > 0 && (
          <ContentRow 
            title="Daily AI Digest Articles" 
            subtitle="Today's curated AI news with audio summary"
          >
            {digestData.articles.map((article) => (
              <ArticleCard
                key={article.id}
                article={article}
                onClick={() => handleArticleClick(article)}
              />
            ))}
          </ContentRow>
        )}

        {/* Source-specific sections */}
        {sources.map((source) => {
          const data = sourceData[source.id as keyof typeof sourceData]
          const isLoading = !data?.data && !data?.error
          const articles = data?.data?.articles || []

          if (isLoading) {
            return <SkeletonRow key={source.id} title={source.label} />
          }

          if (articles.length === 0) {
            return null
          }

          return (
            <ContentRow
              key={source.id}
              id={`section-${source.id}`}
              title={source.label}
              subtitle={source.subtitle}
            >
              {articles.map((article: Article) => (
                <ArticleCard
                  key={article.id}
                  article={article}
                  onClick={() => handleArticleClick(article)}
                  isVideo={source.id === "youtube"}
                />
              ))}
            </ContentRow>
          )
        })}
      </div>

      {/* Article Modal */}
      <ArticleModal
        article={selectedArticle}
        isOpen={isModalOpen}
        onClose={handleCloseModal}
      />
    </div>
  )
}
