import { describe, it, expect, vi, beforeEach } from 'vitest'

// Mock the database modules
const mockDbInstance = {
  unsafe: vi.fn(),
  end: vi.fn(),
}

vi.mock('../../../src/database/connection', () => ({
  getDb: vi.fn(() => mockDbInstance),
}))

vi.mock('../../../src/database/utils', () => ({
  withDatabase: vi.fn(async (url: string, operation: any) => {
    return await operation(mockDbInstance)
  }),
}))

// Now import the modules
import {
  searchArticles,
  getLatestArticles,
  getArticleStats,
  getDigests,
  getDigestById,
  getSourcesMetadata
} from '../../../src/database/news-queries'

const mockDatabaseUrl = 'postgresql://test:test@localhost:5432/test'

describe('News Queries', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('searchArticles', () => {
    it('should search articles with full-text search', async () => {
      const mockArticles = [
        { id: '1', title: 'Test Article', content: 'Test content', published_at: '2023-01-01' }
      ]
      const mockCountResult = [{ count: '1' }]
      
      mockDbInstance.unsafe
        .mockResolvedValueOnce(mockCountResult) // Count query
        .mockResolvedValueOnce(mockArticles)    // Articles query
      
      const result = await searchArticles(mockDatabaseUrl, 'test query', { limit: 20, offset: 0 })
      
      expect(result.articles).toEqual(mockArticles)
      expect(result.total).toBe(1)
      expect(mockDbInstance.unsafe).toHaveBeenCalledTimes(2)
      
      // Verify the search query includes full-text search
      const searchQuery = mockDbInstance.unsafe.mock.calls[0][0]
      expect(searchQuery).toContain('to_tsvector')
      expect(searchQuery).toContain('plainto_tsquery')
    })

    it('should apply source filter', async () => {
      const mockCountResult = [{ count: '5' }]
      const mockArticles = []
      
      mockDbInstance.unsafe
        .mockResolvedValueOnce(mockCountResult)
        .mockResolvedValueOnce(mockArticles)
      
      await searchArticles(mockDatabaseUrl, 'test', { source: 'arxiv', limit: 10 })
      
      const countQuery = mockDbInstance.unsafe.mock.calls[0][0]
      expect(countQuery).toContain('source = $2')
      expect(mockDbInstance.unsafe.mock.calls[0][1]).toContain('arxiv')
    })

    it('should apply relevance score filter', async () => {
      const mockCountResult = [{ count: '3' }]
      const mockArticles = []
      
      mockDbInstance.unsafe
        .mockResolvedValueOnce(mockCountResult)
        .mockResolvedValueOnce(mockArticles)
      
      await searchArticles(mockDatabaseUrl, 'test', { minRelevanceScore: 80 })
      
      const countQuery = mockDbInstance.unsafe.mock.calls[0][0]
      expect(countQuery).toContain('relevance_score >= $2')
      expect(mockDbInstance.unsafe.mock.calls[0][1]).toContain(80)
    })

    it('should handle pagination', async () => {
      const mockCountResult = [{ count: '100' }]
      const mockArticles = []
      
      mockDbInstance.unsafe
        .mockResolvedValueOnce(mockCountResult)
        .mockResolvedValueOnce(mockArticles)
      
      await searchArticles(mockDatabaseUrl, 'test', { limit: 50, offset: 25 })
      
      const articlesQuery = mockDbInstance.unsafe.mock.calls[1][0]
      expect(articlesQuery).toContain('LIMIT $2 OFFSET $3')
      expect(mockDbInstance.unsafe.mock.calls[1][1]).toEqual(['test', 50, 25])
    })
  })

  describe('getLatestArticles', () => {
    it('should get articles from past N hours', async () => {
      const mockArticles = [
        { id: '1', title: 'Recent Article', published_at: new Date().toISOString() }
      ]
      
      mockDbInstance.unsafe.mockResolvedValue(mockArticles)
      
      const result = await getLatestArticles(mockDatabaseUrl, 24)
      
      expect(result).toEqual(mockArticles)
      
      const query = mockDbInstance.unsafe.mock.calls[0][0]
      expect(query).toContain('published_at >= $1')
      expect(query).toContain('is_duplicate = false')
      expect(query).toContain('ORDER BY published_at DESC')
    })

    it('should filter by source', async () => {
      mockDbInstance.unsafe.mockResolvedValue([])
      
      await getLatestArticles(mockDatabaseUrl, 12, { source: 'hackernews' })
      
      const query = mockDbInstance.unsafe.mock.calls[0][0]
      expect(query).toContain('AND source = $2')
      expect(mockDbInstance.unsafe.mock.calls[0][1][1]).toBe('hackernews')
    })

    it('should apply limit', async () => {
      mockDbInstance.unsafe.mockResolvedValue([])
      
      await getLatestArticles(mockDatabaseUrl, 24, { limit: 25 })
      
      const query = mockDbInstance.unsafe.mock.calls[0][0]
      expect(query).toContain('LIMIT 25')
    })
  })

  describe('getArticleStats', () => {
    it('should return comprehensive statistics', async () => {
      const mockStats = {
        total_articles: '1000',
        recent_24h: '50',
        duplicates: '10',
        unique_sources: '5',
        avg_relevance: '85.5'
      }
      
      mockDbInstance.unsafe.mockResolvedValue([mockStats])
      
      const result = await getArticleStats(mockDatabaseUrl)
      
      expect(result).toEqual(mockStats)
      
      const query = mockDbInstance.unsafe.mock.calls[0][0]
      expect(query).toContain('COUNT(*) as total_articles')
      expect(query).toContain("COUNT(CASE WHEN published_at > NOW() - INTERVAL '24 hours'")
      expect(query).toContain('COUNT(CASE WHEN is_duplicate = true')
      expect(query).toContain('COUNT(DISTINCT source)')
      expect(query).toContain('AVG(relevance_score)')
    })

    it('should handle null average relevance', async () => {
      const mockStats = {
        total_articles: '100',
        recent_24h: '5',
        duplicates: '2',
        unique_sources: '3',
        avg_relevance: null
      }
      
      mockDbInstance.unsafe.mockResolvedValue([mockStats])
      
      const result = await getArticleStats(mockDatabaseUrl)
      
      expect(result).toEqual(mockStats)
      expect(mockDbInstance.unsafe.mock.calls[0][0]).toContain('COALESCE(AVG(relevance_score), 0)')
    })
  })

  describe('getDigests', () => {
    it('should get paginated digests', async () => {
      const mockCountResult = [{ count: '5' }]
      const mockDigests = [
        { 
          id: '1', 
          digest_date: '2023-01-01', 
          summary_text: 'Summary',
          article_count: '10'
        }
      ]
      
      mockDbInstance.unsafe
        .mockResolvedValueOnce(mockCountResult)
        .mockResolvedValueOnce(mockDigests)
      
      const result = await getDigests(mockDatabaseUrl, 2, 5)
      
      expect(result.digests).toEqual(mockDigests)
      expect(result.total).toBe(5)
      
      // Check pagination
      const digestsQuery = mockDbInstance.unsafe.mock.calls[1][0]
      expect(digestsQuery).toContain('LIMIT $1 OFFSET $2')
      expect(mockDbInstance.unsafe.mock.calls[1][1]).toEqual([5, 5]) // page 2, perPage 5 = offset 5
    })

    it('should include article count subquery', async () => {
      mockDbInstance.unsafe
        .mockResolvedValueOnce([{ count: '1' }])
        .mockResolvedValueOnce([])
      
      await getDigests(mockDatabaseUrl, 1, 10)
      
      const digestsQuery = mockDbInstance.unsafe.mock.calls[1][0]
      expect(digestsQuery).toContain('SELECT COUNT(*) FROM digest_articles WHERE digest_id = daily_digests.id')
    })
  })

  describe('getDigestById', () => {
    it('should get digest with articles', async () => {
      const mockDigest = [{
        id: '1',
        digest_date: '2023-01-01',
        summary_text: 'Summary',
        total_articles_processed: 50
      }]
      const mockArticles = [
        { id: '1', title: 'Article 1' },
        { id: '2', title: 'Article 2' }
      ]
      
      mockDbInstance.unsafe
        .mockResolvedValueOnce(mockDigest)  // Digest query
        .mockResolvedValueOnce(mockArticles) // Articles query
      
      const result = await getDigestById(mockDatabaseUrl, 'digest-id-123')
      
      expect(result.id).toBe('1')
      expect(result.articles).toEqual(mockArticles)
      
      // Verify queries
      expect(mockDbInstance.unsafe.mock.calls[0][1]).toEqual(['digest-id-123'])
      expect(mockDbInstance.unsafe.mock.calls[1][1]).toEqual(['digest-id-123'])
      
      const articlesQuery = mockDbInstance.unsafe.mock.calls[1][0]
      expect(articlesQuery).toContain('JOIN digest_articles da ON a.id = da.article_id')
      expect(articlesQuery).toContain('ORDER BY a.relevance_score DESC')
    })

    it('should return null for non-existent digest', async () => {
      mockDbInstance.unsafe.mockResolvedValue([]) // Empty result
      
      const result = await getDigestById(mockDatabaseUrl, 'non-existent-id')
      
      expect(result).toBeNull()
      expect(mockDbInstance.unsafe).toHaveBeenCalledTimes(1) // Should not query articles
    })
  })

  describe('getSourcesMetadata', () => {
    it('should get sources with metadata', async () => {
      const mockSources = [
        {
          name: 'arxiv',
          article_count: '500',
          last_published: '2023-01-01',
          avg_relevance_score: '85.0',
          recent_count: '20'
        },
        {
          name: 'hackernews',
          article_count: '300',
          last_published: '2023-01-02',
          avg_relevance_score: '78.5',
          recent_count: '0'
        }
      ]
      
      mockDbInstance.unsafe.mockResolvedValue(mockSources)
      
      const result = await getSourcesMetadata(mockDatabaseUrl)
      
      expect(result).toHaveLength(2)
      expect(result[0].name).toBe('arxiv')
      expect(result[0].display_name).toBe('ArXiv')
      expect(result[0].description).toBe('Latest AI/ML research papers')
      expect(result[0].status).toBe('active') // recent_count > 0
      
      expect(result[1].name).toBe('hackernews')
      expect(result[1].display_name).toBe('Hacker News')
      expect(result[1].status).toBe('inactive') // recent_count = 0
      
      const query = mockDbInstance.unsafe.mock.calls[0][0]
      expect(query).toContain('GROUP BY source')
      expect(query).toContain('ORDER BY article_count DESC')
      expect(query).toContain("COUNT(CASE WHEN published_at > NOW() - INTERVAL '7 days'")
    })

    it('should handle unknown sources with fallback names', async () => {
      const mockSources = [
        {
          name: 'unknown_source',
          article_count: '10',
          last_published: '2023-01-01',
          avg_relevance_score: '70.0',
          recent_count: '1'
        }
      ]
      
      mockDbInstance.unsafe.mockResolvedValue(mockSources)
      
      const result = await getSourcesMetadata(mockDatabaseUrl)
      
      expect(result[0].name).toBe('unknown_source')
      expect(result[0].display_name).toBe('unknown_source') // Fallback to source name
      expect(result[0].description).toBe('AI/ML news source') // Fallback description
    })
  })
})