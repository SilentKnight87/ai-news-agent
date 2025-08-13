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

// Mock news queries module
vi.mock('../../../src/database/news-queries', () => ({
  searchArticles: vi.fn(),
  getLatestArticles: vi.fn(),
  getArticleStats: vi.fn(),
  getDigests: vi.fn(),
  getDigestById: vi.fn(),
  getSourcesMetadata: vi.fn(),
}))

// Now import the modules
import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { registerNewsTools } from '../../../src/tools/news-tools'
import { mockProps } from '../../fixtures/auth.fixtures'
import * as newsQueries from '../../../src/database/news-queries'

// Get the mocked functions
const mockNewsQueries = newsQueries as any

// Mock environment with CACHE binding
const mockCache = {
  get: vi.fn(),
  put: vi.fn(),
  delete: vi.fn(),
}

const mockEnvWithCache = {
  GITHUB_CLIENT_ID: 'test-client-id',
  GITHUB_CLIENT_SECRET: 'test-client-secret',
  COOKIE_ENCRYPTION_KEY: 'test-encryption-key',
  DATABASE_URL: 'postgresql://test:test@localhost:5432/test',
  CACHE: mockCache,
}

// Test data
const mockArticles = [
  {
    id: '1',
    title: 'Test Article 1',
    content: 'Test content 1',
    source: 'arxiv',
    published_at: '2023-01-01T00:00:00Z',
    relevance_score: 85,
  },
  {
    id: '2',
    title: 'Test Article 2',
    content: 'Test content 2',
    source: 'hackernews',
    published_at: '2023-01-02T00:00:00Z',
    relevance_score: 90,
  },
]

const mockSearchResult = {
  articles: mockArticles,
  total: 2,
}

const mockStats = {
  total_articles: 1000,
  recent_24h: 50,
  duplicates: 10,
  unique_sources: 5,
  avg_relevance: 85.5,
}

const mockDigests = [
  {
    id: '1',
    digest_date: '2023-01-01',
    summary_text: 'Daily digest summary',
    total_articles_processed: 50,
    article_count: 10,
  },
]

const mockDigestResult = {
  digests: mockDigests,
  total: 1,
}

const mockDigestWithArticles = {
  id: '1',
  digest_date: '2023-01-01',
  summary_text: 'Daily digest summary',
  total_articles_processed: 50,
  articles: mockArticles,
}

const mockSources = [
  {
    name: 'arxiv',
    display_name: 'ArXiv',
    description: 'Latest AI/ML research papers',
    article_count: 500,
    status: 'active',
  },
  {
    name: 'hackernews',
    display_name: 'Hacker News',
    description: 'Tech news and discussions',
    article_count: 300,
    status: 'active',
  },
]

describe('News Tools', () => {
  let mockServer: McpServer
  
  beforeEach(() => {
    vi.clearAllMocks()
    mockServer = new McpServer({ name: 'test', version: '1.0.0' })
    
    // Setup mock returns
    mockNewsQueries.searchArticles.mockResolvedValue(mockSearchResult)
    mockNewsQueries.getLatestArticles.mockResolvedValue(mockArticles)
    mockNewsQueries.getArticleStats.mockResolvedValue(mockStats)
    mockNewsQueries.getDigests.mockResolvedValue(mockDigestResult)
    mockNewsQueries.getDigestById.mockResolvedValue(mockDigestWithArticles)
    mockNewsQueries.getSourcesMetadata.mockResolvedValue(mockSources)
    
    // Setup cache mocks
    mockCache.get.mockResolvedValue(null) // No cache by default
    mockCache.put.mockResolvedValue(undefined)
  })

  describe('registerNewsTools', () => {
    it('should register all 6 news tools', () => {
      const toolSpy = vi.spyOn(mockServer, 'tool')
      
      registerNewsTools(mockServer, mockEnvWithCache as any, mockProps)
      
      expect(toolSpy).toHaveBeenCalledWith(
        'search_articles',
        expect.any(String),
        expect.any(Object),
        expect.any(Function)
      )
      expect(toolSpy).toHaveBeenCalledWith(
        'get_latest_articles',
        expect.any(String),
        expect.any(Object),
        expect.any(Function)
      )
      expect(toolSpy).toHaveBeenCalledWith(
        'get_article_stats',
        expect.any(String),
        expect.any(Object),
        expect.any(Function)
      )
      expect(toolSpy).toHaveBeenCalledWith(
        'get_digests',
        expect.any(String),
        expect.any(Object),
        expect.any(Function)
      )
      expect(toolSpy).toHaveBeenCalledWith(
        'get_digest_by_id',
        expect.any(String),
        expect.any(Object),
        expect.any(Function)
      )
      expect(toolSpy).toHaveBeenCalledWith(
        'get_sources',
        expect.any(String),
        expect.any(Object),
        expect.any(Function)
      )
      expect(toolSpy).toHaveBeenCalledTimes(6)
    })
  })

  describe('search_articles tool', () => {
    it('should search articles successfully', async () => {
      const toolSpy = vi.spyOn(mockServer, 'tool')
      registerNewsTools(mockServer, mockEnvWithCache as any, mockProps)
      
      const toolCall = toolSpy.mock.calls.find(call => call[0] === 'search_articles')
      const handler = toolCall![3] as Function
      
      const result = await handler({
        query: 'machine learning',
        limit: 20,
        offset: 0
      })
      
      expect(mockNewsQueries.searchArticles).toHaveBeenCalledWith(
        mockEnvWithCache.DATABASE_URL,
        'machine learning',
        { limit: 20, offset: 0, minRelevanceScore: undefined, source: undefined }
      )
      expect(result.content[0].type).toBe('text')
      expect(result.content[0].text).toContain('Search Results')
      expect(result.content[0].text).toContain('machine learning')
      expect(result.content[0].text).toContain('2 total results')
    })

    it('should use cached results when available', async () => {
      mockCache.get.mockResolvedValue(mockSearchResult)
      
      const toolSpy = vi.spyOn(mockServer, 'tool')
      registerNewsTools(mockServer, mockEnvWithCache as any, mockProps)
      
      const toolCall = toolSpy.mock.calls.find(call => call[0] === 'search_articles')
      const handler = toolCall![3] as Function
      
      const result = await handler({
        query: 'machine learning',
        limit: 20,
        offset: 0
      })
      
      expect(mockNewsQueries.searchArticles).not.toHaveBeenCalled()
      expect(result.content[0].text).toContain('Cached Search Results')
    })

    it('should handle search errors', async () => {
      mockNewsQueries.searchArticles.mockRejectedValue(new Error('Database connection failed'))
      
      const toolSpy = vi.spyOn(mockServer, 'tool')
      registerNewsTools(mockServer, mockEnvWithCache as any, mockProps)
      
      const toolCall = toolSpy.mock.calls.find(call => call[0] === 'search_articles')
      const handler = toolCall![3] as Function
      
      const result = await handler({
        query: 'machine learning',
        limit: 20,
        offset: 0
      })
      
      expect(result.content[0].isError).toBe(true)
      expect(result.content[0].text).toContain('Failed to search articles')
    })
  })

  describe('get_latest_articles tool', () => {
    it('should get latest articles successfully', async () => {
      const toolSpy = vi.spyOn(mockServer, 'tool')
      registerNewsTools(mockServer, mockEnvWithCache as any, mockProps)
      
      const toolCall = toolSpy.mock.calls.find(call => call[0] === 'get_latest_articles')
      const handler = toolCall![3] as Function
      
      const result = await handler({
        hours: 24,
        limit: 50
      })
      
      expect(mockNewsQueries.getLatestArticles).toHaveBeenCalledWith(
        mockEnvWithCache.DATABASE_URL,
        24,
        { limit: 50, minRelevanceScore: undefined, source: undefined }
      )
      expect(result.content[0].type).toBe('text')
      expect(result.content[0].text).toContain('Latest Articles')
      expect(result.content[0].text).toContain('From past 24 hours')
      expect(result.content[0].text).toContain('2 articles found')
    })

    it('should handle latest articles errors', async () => {
      mockNewsQueries.getLatestArticles.mockRejectedValue(new Error('Query failed'))
      
      const toolSpy = vi.spyOn(mockServer, 'tool')
      registerNewsTools(mockServer, mockEnvWithCache as any, mockProps)
      
      const toolCall = toolSpy.mock.calls.find(call => call[0] === 'get_latest_articles')
      const handler = toolCall![3] as Function
      
      const result = await handler({
        hours: 24,
        limit: 50
      })
      
      expect(result.content[0].isError).toBe(true)
      expect(result.content[0].text).toContain('Failed to get latest articles')
    })
  })

  describe('get_article_stats tool', () => {
    it('should get statistics successfully', async () => {
      const toolSpy = vi.spyOn(mockServer, 'tool')
      registerNewsTools(mockServer, mockEnvWithCache as any, mockProps)
      
      const toolCall = toolSpy.mock.calls.find(call => call[0] === 'get_article_stats')
      const handler = toolCall![3] as Function
      
      const result = await handler({})
      
      expect(mockNewsQueries.getArticleStats).toHaveBeenCalledWith(mockEnvWithCache.DATABASE_URL)
      expect(result.content[0].type).toBe('text')
      expect(result.content[0].text).toContain('Database Statistics')
      expect(result.content[0].text).toContain('Total Articles: 1000')
      expect(result.content[0].text).toContain('Last 24 Hours: 50')
      expect(result.content[0].text).toContain('Average Relevance: 86%')
    })

    it('should handle stats errors', async () => {
      mockNewsQueries.getArticleStats.mockRejectedValue(new Error('Stats query failed'))
      
      const toolSpy = vi.spyOn(mockServer, 'tool')
      registerNewsTools(mockServer, mockEnvWithCache as any, mockProps)
      
      const toolCall = toolSpy.mock.calls.find(call => call[0] === 'get_article_stats')
      const handler = toolCall![3] as Function
      
      const result = await handler({})
      
      expect(result.content[0].isError).toBe(true)
      expect(result.content[0].text).toContain('Failed to get statistics')
    })
  })

  describe('get_digests tool', () => {
    it('should get digests successfully', async () => {
      const toolSpy = vi.spyOn(mockServer, 'tool')
      registerNewsTools(mockServer, mockEnvWithCache as any, mockProps)
      
      const toolCall = toolSpy.mock.calls.find(call => call[0] === 'get_digests')
      const handler = toolCall![3] as Function
      
      const result = await handler({
        page: 1,
        per_page: 10
      })
      
      expect(mockNewsQueries.getDigests).toHaveBeenCalledWith(
        mockEnvWithCache.DATABASE_URL,
        1,
        10
      )
      expect(result.content[0].type).toBe('text')
      expect(result.content[0].text).toContain('Daily Digests')
      expect(result.content[0].text).toContain('Page 1 of 1')
      expect(result.content[0].text).toContain('Total: 1 digests')
    })

    it('should handle digests errors', async () => {
      mockNewsQueries.getDigests.mockRejectedValue(new Error('Digests query failed'))
      
      const toolSpy = vi.spyOn(mockServer, 'tool')
      registerNewsTools(mockServer, mockEnvWithCache as any, mockProps)
      
      const toolCall = toolSpy.mock.calls.find(call => call[0] === 'get_digests')
      const handler = toolCall![3] as Function
      
      const result = await handler({
        page: 1,
        per_page: 10
      })
      
      expect(result.content[0].isError).toBe(true)
      expect(result.content[0].text).toContain('Failed to get digests')
    })
  })

  describe('get_digest_by_id tool', () => {
    it('should get digest by ID successfully', async () => {
      const toolSpy = vi.spyOn(mockServer, 'tool')
      registerNewsTools(mockServer, mockEnvWithCache as any, mockProps)
      
      const toolCall = toolSpy.mock.calls.find(call => call[0] === 'get_digest_by_id')
      const handler = toolCall![3] as Function
      
      const result = await handler({
        digest_id: '123e4567-e89b-12d3-a456-426614174000'
      })
      
      expect(mockNewsQueries.getDigestById).toHaveBeenCalledWith(
        mockEnvWithCache.DATABASE_URL,
        '123e4567-e89b-12d3-a456-426614174000'
      )
      expect(result.content[0].type).toBe('text')
      expect(result.content[0].text).toContain('Daily Digest')
      expect(result.content[0].text).toContain('Daily digest summary')
      expect(result.content[0].text).toContain('Articles: 2')
    })

    it('should handle digest not found', async () => {
      mockNewsQueries.getDigestById.mockResolvedValue(null)
      
      const toolSpy = vi.spyOn(mockServer, 'tool')
      registerNewsTools(mockServer, mockEnvWithCache as any, mockProps)
      
      const toolCall = toolSpy.mock.calls.find(call => call[0] === 'get_digest_by_id')
      const handler = toolCall![3] as Function
      
      const result = await handler({
        digest_id: '123e4567-e89b-12d3-a456-426614174000'
      })
      
      expect(result.content[0].isError).toBe(true)
      expect(result.content[0].text).toContain('Digest not found')
    })

    it('should handle digest errors', async () => {
      mockNewsQueries.getDigestById.mockRejectedValue(new Error('Digest query failed'))
      
      const toolSpy = vi.spyOn(mockServer, 'tool')
      registerNewsTools(mockServer, mockEnvWithCache as any, mockProps)
      
      const toolCall = toolSpy.mock.calls.find(call => call[0] === 'get_digest_by_id')
      const handler = toolCall![3] as Function
      
      const result = await handler({
        digest_id: '123e4567-e89b-12d3-a456-426614174000'
      })
      
      expect(result.content[0].isError).toBe(true)
      expect(result.content[0].text).toContain('Failed to get digest')
    })
  })

  describe('get_sources tool', () => {
    it('should get sources successfully', async () => {
      const toolSpy = vi.spyOn(mockServer, 'tool')
      registerNewsTools(mockServer, mockEnvWithCache as any, mockProps)
      
      const toolCall = toolSpy.mock.calls.find(call => call[0] === 'get_sources')
      const handler = toolCall![3] as Function
      
      const result = await handler({})
      
      expect(mockNewsQueries.getSourcesMetadata).toHaveBeenCalledWith(mockEnvWithCache.DATABASE_URL)
      expect(result.content[0].type).toBe('text')
      expect(result.content[0].text).toContain('News Sources')
      expect(result.content[0].text).toContain('Total: 2 sources')
      expect(result.content[0].text).toContain('Active: 2 sources')
    })

    it('should handle sources errors', async () => {
      mockNewsQueries.getSourcesMetadata.mockRejectedValue(new Error('Sources query failed'))
      
      const toolSpy = vi.spyOn(mockServer, 'tool')
      registerNewsTools(mockServer, mockEnvWithCache as any, mockProps)
      
      const toolCall = toolSpy.mock.calls.find(call => call[0] === 'get_sources')
      const handler = toolCall![3] as Function
      
      const result = await handler({})
      
      expect(result.content[0].isError).toBe(true)
      expect(result.content[0].text).toContain('Failed to get sources')
    })
  })

  describe('caching behavior', () => {
    it('should cache search results', async () => {
      const toolSpy = vi.spyOn(mockServer, 'tool')
      registerNewsTools(mockServer, mockEnvWithCache as any, mockProps)
      
      const toolCall = toolSpy.mock.calls.find(call => call[0] === 'search_articles')
      const handler = toolCall![3] as Function
      
      await handler({
        query: 'machine learning',
        limit: 20,
        offset: 0
      })
      
      expect(mockCache.put).toHaveBeenCalledWith(
        expect.stringContaining('search:machine learning'),
        JSON.stringify(mockSearchResult),
        { expirationTtl: 300 }
      )
    })

    it('should cache statistics with 1 hour TTL', async () => {
      const toolSpy = vi.spyOn(mockServer, 'tool')
      registerNewsTools(mockServer, mockEnvWithCache as any, mockProps)
      
      const toolCall = toolSpy.mock.calls.find(call => call[0] === 'get_article_stats')
      const handler = toolCall![3] as Function
      
      await handler({})
      
      expect(mockCache.put).toHaveBeenCalledWith(
        'stats:global',
        JSON.stringify(mockStats),
        { expirationTtl: 3600 }
      )
    })
  })
})