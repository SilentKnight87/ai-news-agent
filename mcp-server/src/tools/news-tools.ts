import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";
import { Props, createSuccessResponse, createErrorResponse } from "../types";
import * as newsQueries from '../database/news-queries';

// Input validation schemas
const SearchArticlesSchema = {
  query: z.string().min(1).max(200).describe("Search query"),
  source: z.string().optional().describe("Filter by source (arxiv, hackernews, reddit_machinelearning, etc)"),
  limit: z.number().int().positive().max(100).default(20).describe("Number of results"),
  offset: z.number().int().min(0).default(0).describe("Pagination offset"),
  minRelevanceScore: z.number().min(0).max(100).optional().describe("Minimum relevance score filter")
};

const GetLatestArticlesSchema = {
  hours: z.number().int().positive().max(168).default(24).describe("Get articles from past N hours"),
  source: z.string().optional().describe("Filter by source"),
  limit: z.number().int().positive().max(100).default(50).describe("Number of results"),
  minRelevanceScore: z.number().min(0).max(100).optional().describe("Minimum relevance score filter")
};

const GetDigestsSchema = {
  page: z.number().int().positive().default(1).describe("Page number"),
  per_page: z.number().int().positive().max(50).default(10).describe("Items per page")
};

const GetDigestByIdSchema = {
  digest_id: z.string().uuid().describe("Digest UUID")
};

const GetSourcesSchema = {};

export function registerNewsTools(server: McpServer, env: Env, props: Props) {
  console.log(`Registering news tools for user: ${props.login}`);

  // Tool 1: Search Articles
  server.tool(
    "search_articles",
    "Search AI/ML news articles using full-text search. Returns articles matching the query with relevance scores.",
    SearchArticlesSchema,
    async ({ query, source, limit, offset, minRelevanceScore }) => {
      try {
        const startTime = Date.now();
        
        // Check cache first
        const cacheKey = `search:${query}:${source}:${limit}:${offset}:${minRelevanceScore}`;
        const cached = await env.CACHE?.get(cacheKey, "json") as any;
        if (cached) {
          return createSuccessResponse(
            `Cached Search Results - Query: "${query}" - ${cached.total} total results`,
            cached
          );
        }
        
        // Execute search
        const result = await newsQueries.searchArticles(
          env.DATABASE_URL,
          query,
          { source, limit, offset, minRelevanceScore }
        );
        
        // Cache for 5 minutes
        await env.CACHE?.put(cacheKey, JSON.stringify(result), { expirationTtl: 300 });
        
        const duration = Date.now() - startTime;
        
        return createSuccessResponse(
          `Search Results - Query: "${query}" - ${result.total} total results (${duration}ms)`,
          result
        );
      } catch (error) {
        console.error("Search articles error:", error);
        return createErrorResponse(
          `Failed to search articles: ${error instanceof Error ? error.message : String(error)}`
        );
      }
    }
  );

  // Tool 2: Get Latest Articles
  server.tool(
    "get_latest_articles",
    "Get the most recent AI/ML news articles from the past N hours. Default is 24 hours.",
    GetLatestArticlesSchema,
    async ({ hours, source, limit, minRelevanceScore }) => {
      try {
        const cacheKey = `latest:${hours}:${source}:${limit}:${minRelevanceScore}`;
        const cached = await env.CACHE?.get(cacheKey, "json");
        if (cached) {
          return createSuccessResponse(
            `Cached Latest Articles - From past ${hours} hours - ${cached.length} articles`,
            cached
          );
        }
        
        const articles = await newsQueries.getLatestArticles(
          env.DATABASE_URL,
          hours,
          { source, limit, minRelevanceScore }
        );
        
        // Cache for 10 minutes
        await env.CACHE?.put(cacheKey, JSON.stringify(articles), { expirationTtl: 600 });
        
        return createSuccessResponse(
          `Latest Articles - From past ${hours} hours - ${articles.length} articles found`,
          articles
        );
      } catch (error) {
        console.error("Get latest articles error:", error);
        return createErrorResponse(
          `Failed to get latest articles: ${error instanceof Error ? error.message : String(error)}`
        );
      }
    }
  );

  // Tool 3: Get Statistics
  server.tool(
    "get_article_stats",
    "Get comprehensive statistics about the AI news database including total articles, sources, and trends.",
    {},
    async () => {
      try {
        const cacheKey = `stats:global`;
        const cached = await env.CACHE?.get(cacheKey, "json");
        if (cached) {
          return createSuccessResponse(
            "Cached Database Statistics",
            cached
          );
        }

        const stats = await newsQueries.getArticleStats(env.DATABASE_URL);
        
        // Cache for 1 hour
        await env.CACHE?.put(cacheKey, JSON.stringify(stats), { expirationTtl: 3600 });
        
        return createSuccessResponse(
          "Database Statistics",
          stats
        );
      } catch (error) {
        console.error("Get stats error:", error);
        return createErrorResponse(
          `Failed to get statistics: ${error instanceof Error ? error.message : String(error)}`
        );
      }
    }
  );

  // Tool 4: Get Daily Digests
  server.tool(
    "get_digests",
    "Get paginated list of daily AI news digests with summaries and key developments.",
    GetDigestsSchema,
    async ({ page, per_page }) => {
      try {
        const cacheKey = `digests:${page}:${per_page}`;
        const cached = await env.CACHE?.get(cacheKey, "json");
        if (cached) {
          const totalPages = Math.ceil(cached.total / per_page);
          return createSuccessResponse(
            `Cached Daily Digests - Page ${page} of ${totalPages} - Total: ${cached.total} digests`,
            cached
          );
        }

        const result = await newsQueries.getDigests(
          env.DATABASE_URL,
          page,
          per_page
        );
        
        // Cache for 1 hour
        await env.CACHE?.put(cacheKey, JSON.stringify(result), { expirationTtl: 3600 });
        
        const totalPages = Math.ceil(result.total / per_page);
        
        return createSuccessResponse(
          `Daily Digests - Page ${page} of ${totalPages} - Total: ${result.total} digests`,
          result
        );
      } catch (error) {
        console.error("Get digests error:", error);
        return createErrorResponse(
          `Failed to get digests: ${error instanceof Error ? error.message : String(error)}`
        );
      }
    }
  );

  // Tool 5: Get Single Digest
  server.tool(
    "get_digest_by_id",
    "Get a specific daily digest with all its articles and detailed information.",
    GetDigestByIdSchema,
    async ({ digest_id }) => {
      try {
        const cacheKey = `digest:${digest_id}`;
        const cached = await env.CACHE?.get(cacheKey, "json");
        if (cached) {
          return createSuccessResponse(
            `Cached Daily Digest - Date: ${cached.digest_date} - Articles: ${cached.articles.length}`,
            cached
          );
        }

        const digest = await newsQueries.getDigestById(
          env.DATABASE_URL,
          digest_id
        );
        
        if (!digest) {
          return createErrorResponse(`Digest not found with ID: ${digest_id}`);
        }
        
        // Cache for 24 hours
        await env.CACHE?.put(cacheKey, JSON.stringify(digest), { expirationTtl: 86400 });
        
        return createSuccessResponse(
          `Daily Digest - Date: ${digest.digest_date} - Articles: ${digest.articles.length}`,
          digest
        );
      } catch (error) {
        console.error("Get digest by ID error:", error);
        return createErrorResponse(
          `Failed to get digest: ${error instanceof Error ? error.message : String(error)}`
        );
      }
    }
  );

  // Tool 6: Get Sources Metadata
  server.tool(
    "get_sources",
    "Get metadata about all AI news sources including article counts and activity status.",
    {},
    async () => {
      try {
        const cacheKey = `sources:metadata`;
        const cached = await env.CACHE?.get(cacheKey, "json");
        if (cached) {
          const activeSources = cached.filter((s: any) => s.status === 'active').length;
          return createSuccessResponse(
            `Cached News Sources - Total: ${cached.length} sources - Active: ${activeSources} sources`,
            cached
          );
        }

        const sources = await newsQueries.getSourcesMetadata(env.DATABASE_URL);
        
        // Cache for 24 hours
        await env.CACHE?.put(cacheKey, JSON.stringify(sources), { expirationTtl: 86400 });
        
        const activeSources = sources.filter(s => s.status === 'active').length;
        
        return createSuccessResponse(
          `News Sources - Total: ${sources.length} sources - Active: ${activeSources} sources`,
          sources
        );
      } catch (error) {
        console.error("Get sources error:", error);
        return createErrorResponse(
          `Failed to get sources: ${error instanceof Error ? error.message : String(error)}`
        );
      }
    }
  );

  console.log(`Registered 6 news tools for user: ${props.login}`);
}