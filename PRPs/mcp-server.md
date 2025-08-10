name: "MCP Server Implementation - AI News Aggregator Tools PRP"
description: |

## Purpose
Implement a Model Context Protocol (MCP) server in Python that exposes AI News Aggregator data and tools to AI assistants (Claude, Cursor, etc.). The server will leverage existing backend services for content retrieval, analysis, and export capabilities.

## Core Principles
1. **Reuse Backend**: Direct Python imports of existing backend services (no HTTP duplication)
2. **MCP Compliance**: Follow MCP specification for JSON-RPC 2.0 protocol
3. **Async First**: Use existing async patterns from backend services
4. **Rate Limit Respect**: Inherit backend rate limiting (ArXiv 3s, HN 1req/s)
5. **Error Resilience**: Circuit breaker patterns from existing backend

---

## Goal
Create an MCP server that exposes 6 MVP tools for AI assistants to interact with the news aggregator, enabling content retrieval, search, summarization, and digest generation through the MCP protocol.

## Why
- **AI Assistant Integration**: Enable Claude, Cursor to access aggregated AI news
- **Direct Data Access**: AI assistants can query and analyze content directly
- **Leverage Existing**: All backend services ready to be exposed via MCP
- **MVP Critical**: MCP server listed as critical requirement for v1

## What
MCP server with:
- 6 MVP tools (arxiv, hackernews, rss, search, summarize, digest)
- Direct backend service integration (no HTTP calls)
- Proper MCP protocol implementation with JSON-RPC 2.0
- Error handling and rate limiting from backend
- Authentication via environment variables
- Async tool implementations

### Success Criteria
- [ ] All 6 MVP tools working with Claude Desktop
- [ ] Rate limits respected (ArXiv 3s delay maintained)
- [ ] Search returns results in < 500ms
- [ ] Summarization uses existing PydanticAI agents
- [ ] Digest generation leverages existing workflow
- [ ] Error messages propagate correctly to MCP clients
- [ ] All tests pass with > 90% coverage

## All Needed Context

### Documentation & References
```yaml
# MUST READ - Include these in your context window
- file: src/fetchers/arxiv_fetcher.py
  why: ArXiv fetcher patterns with rate limiting
  
- file: src/fetchers/hackernews_fetcher.py
  why: HackerNews fetcher implementation
  
- file: src/fetchers/rss_fetcher.py
  why: RSS fetcher with dynamic feed management
  
- file: src/repositories/articles.py
  why: Search and filter implementations
  
- file: src/agents/news_agent.py
  why: Summarization agent patterns
  
- file: src/agents/digest_agent.py
  why: Digest generation workflow
  
- file: src/config.py
  why: Configuration and environment patterns
  
- file: src/main.py
  why: FastAPI app structure for reference
  
- docfile: spec/mcp-server.md
  why: Complete specification with tool definitions

# External Documentation via MCP
- mcp: mcp__context7__resolve-library-id
  params: "mcp"
  then: mcp__context7__get-library-docs("/modelcontextprotocol/python-sdk", topic="server,tools")
  why: MCP Python SDK patterns
  
- url: https://spec.modelcontextprotocol.io/specification/server/tools/
  section: Tool definition and response formats
  critical: Must follow exact JSON-RPC format
  
- url: https://github.com/modelcontextprotocol/python-sdk/tree/main/examples
  why: Example MCP server implementations in Python
  
- url: https://docs.anthropic.com/en/docs/build-with-claude/mcp
  section: Claude MCP integration requirements
```

### Current Codebase Structure
```bash
src/
├── agents/           # AI agents (news, digest)
├── fetchers/         # Content fetchers (arxiv, hn, rss)
├── repositories/     # Data access (search, filter)
├── services/         # Core services (embeddings, TTS)
├── api/             # FastAPI routes
├── models/          # Pydantic models
└── config.py        # Configuration management

mcp-server/          # Existing TypeScript template (ignore)
```

### Desired Structure with New Files
```bash
src/
├── mcp/
│   ├── __init__.py
│   ├── server.py           # Main MCP server implementation
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── content.py      # Content retrieval tools
│   │   ├── analysis.py     # Analysis and summary tools
│   │   └── export.py       # Export and digest tools
│   ├── handlers.py         # JSON-RPC request handlers
│   ├── errors.py          # MCP error definitions
│   └── types.py           # MCP type definitions
├── mcp_main.py            # MCP server entry point
└── tests/
    └── test_mcp/
        ├── test_server.py
        ├── test_tools.py
        └── test_handlers.py
```

### Known Gotchas & Critical Context
```python
# CRITICAL: MCP uses JSON-RPC 2.0 format
# Request: {"jsonrpc": "2.0", "method": "tools/call", "params": {...}, "id": 1}
# Response: {"jsonrpc": "2.0", "result": {...}, "id": 1}

# CRITICAL: Tool names must be lowercase with underscores
# Good: get_latest_arxiv_papers
# Bad: getLatestArxivPapers, get-latest-arxiv-papers

# CRITICAL: ArXiv rate limit is 3 seconds
# Must use existing arxiv_fetcher with delay_seconds=3.0
# Never bypass this or risk IP ban

# PATTERN: Import backend services directly
# from src.fetchers.arxiv_fetcher import ArxivFetcher
# NOT: requests.get("http://localhost:8000/api/...")

# PATTERN: Use existing async patterns
# All backend services are async-ready
# MCP tools must be async def

# GOTCHA: MCP server runs separately from FastAPI
# Different port (default 3000 for MCP)
# Can share same .env configuration

# GOTCHA: Error handling
# MCP expects specific error codes
# -32700: Parse error
# -32600: Invalid request
# -32601: Method not found
# -32602: Invalid params
# -32603: Internal error

# PATTERN: Authentication
# MCP server should validate API keys from env
# Use same pattern as FastAPI dependencies
```

## Implementation Blueprint

### Data Models
```python
# src/mcp/types.py - MCP type definitions

from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field
from enum import Enum

class MCPRequest(BaseModel):
    """JSON-RPC 2.0 request format."""
    jsonrpc: str = "2.0"
    method: str
    params: Optional[Dict[str, Any]] = None
    id: Optional[Union[str, int]] = None

class MCPResponse(BaseModel):
    """JSON-RPC 2.0 response format."""
    jsonrpc: str = "2.0"
    result: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None
    id: Optional[Union[str, int]] = None

class ToolDefinition(BaseModel):
    """MCP tool definition."""
    name: str
    description: str
    input_schema: Dict[str, Any]

class ToolCallParams(BaseModel):
    """Parameters for tool execution."""
    name: str
    arguments: Optional[Dict[str, Any]] = Field(default_factory=dict)

class ToolResult(BaseModel):
    """Result from tool execution."""
    content: List[Dict[str, Any]]
    is_error: bool = False

class ServerCapabilities(BaseModel):
    """MCP server capabilities."""
    tools: Dict[str, bool] = {"listChanged": True}
    resources: Optional[Dict[str, bool]] = None
    prompts: Optional[Dict[str, bool]] = None
```

### Task List

```yaml
Task 1: Install MCP Python SDK
EXECUTE:
  pip install mcp

Task 2: Create MCP Type Definitions
CREATE src/mcp/types.py:
  - DEFINE: MCPRequest, MCPResponse models
  - DEFINE: ToolDefinition, ToolCallParams
  - FOLLOW: MCP specification exactly
  - PATTERN: Use Pydantic for validation

Task 3: Create Error Definitions
CREATE src/mcp/errors.py:
  - DEFINE: MCP error codes and messages
  - MAP: Backend exceptions to MCP errors
  - INCLUDE: Rate limit errors
  - PATTERN: Inherit from existing error classes

Task 4: Create Content Retrieval Tools
CREATE src/mcp/tools/content.py:
  - TOOL: get_latest_arxiv_papers
    - Import: ArxivFetcher from backend
    - Params: categories, max_results
    - Respect: 3-second rate limit
  - TOOL: get_hackernews_stories
    - Import: HackerNewsFetcher
    - Params: story_type, limit
  - TOOL: get_rss_feed_articles
    - Import: RSSFetcher
    - Params: feed_names, limit
  - PATTERN: Direct service imports

Task 5: Create Analysis Tools
CREATE src/mcp/tools/analysis.py:
  - TOOL: search_content
    - Import: ArticleRepository
    - Use: search_articles method
    - Params: query, source, limit
  - TOOL: summarize_article
    - Import: NewsAnalyzer agent
    - Use: analyze_article method
    - Params: article_id or content
  - PATTERN: Reuse existing agents

Task 6: Create Export Tools
CREATE src/mcp/tools/export.py:
  - TOOL: generate_daily_digest
    - Import: DigestAgent
    - Use: generate_digest method
    - Params: date, min_relevance
  - FUTURE: export_articles (Tier 1)
  - PATTERN: Async digest generation

Task 7: Create Request Handlers
CREATE src/mcp/handlers.py:
  - HANDLE: initialize request
  - HANDLE: tools/list request
  - HANDLE: tools/call request
  - ROUTING: Method to handler mapping
  - ERROR: Proper JSON-RPC error responses

Task 8: Create Main MCP Server
CREATE src/mcp/server.py:
  - CLASS: MCPServer with tool registry
  - INIT: Load all tools dynamically
  - SERVE: Handle JSON-RPC over stdio
  - AUTH: Validate API keys from env
  - LOG: Request/response logging

Task 9: Create Server Entry Point
CREATE src/mcp_main.py:
  - SETUP: Async event loop
  - CONFIG: Load from .env
  - START: MCP server on stdio
  - SIGNAL: Handle shutdown gracefully

Task 10: Create Tool Tests
CREATE tests/test_mcp/test_tools.py:
  - TEST: Each tool with mock data
  - VERIFY: Rate limiting respected
  - CHECK: Error handling
  - MOCK: Backend services

Task 11: Create Handler Tests
CREATE tests/test_mcp/test_handlers.py:
  - TEST: JSON-RPC request parsing
  - TEST: Method routing
  - TEST: Error responses
  - TEST: Initialize flow

Task 12: Create Integration Tests
CREATE tests/test_mcp/test_integration.py:
  - TEST: Full request/response cycle
  - TEST: Tool execution end-to-end
  - MOCK: External dependencies
  - VERIFY: MCP compliance

Task 13: Create Claude Config
CREATE claude_mcp_config.json:
  - CONFIG: Server command
  - ENV: Required variables
  - SCHEMA: Tool definitions

Task 14: Documentation
CREATE mcp-server/README.md:
  - USAGE: Installation steps
  - CONFIG: Claude Desktop setup
  - TOOLS: Full tool documentation
  - EXAMPLES: Usage examples
```

### Per-Task Implementation Details

```python
# Task 4: Content Retrieval Tools
# src/mcp/tools/content.py
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from src.fetchers.arxiv_fetcher import ArxivFetcher
from src.fetchers.hackernews_fetcher import HackerNewsFetcher
from src.fetchers.rss_fetcher import RSSFetcher
from src.models.articles import Article
from ..types import ToolResult

class ContentTools:
    """Content retrieval tools for MCP."""
    
    def __init__(self):
        """Initialize fetchers."""
        self.arxiv = ArxivFetcher()
        self.hackernews = HackerNewsFetcher()
        self.rss = RSSFetcher()
    
    async def get_latest_arxiv_papers(
        self,
        categories: Optional[List[str]] = None,
        max_results: int = 10,
        days_back: int = 7
    ) -> ToolResult:
        """
        Fetch recent AI/ML papers from ArXiv.
        
        CRITICAL: Respects 3-second rate limit automatically.
        """
        try:
            # Use existing fetcher with built-in rate limiting
            articles = await self.arxiv.fetch(
                max_articles=max_results,
                since_days=days_back
            )
            
            # Format for MCP response
            content = []
            for article in articles:
                content.append({
                    "type": "text",
                    "text": f"**{article.title}**\n"
                           f"Authors: {article.author}\n"
                           f"URL: {article.url}\n"
                           f"Summary: {article.content[:500]}...\n"
                           f"Published: {article.published_at.isoformat()}"
                })
            
            return ToolResult(content=content)
            
        except Exception as e:
            return ToolResult(
                content=[{"type": "text", "text": f"Error fetching ArXiv papers: {str(e)}"}],
                is_error=True
            )
    
    async def get_hackernews_stories(
        self,
        story_type: str = "top",
        limit: int = 10,
        min_score: int = 50
    ) -> ToolResult:
        """
        Fetch top HackerNews stories related to AI/ML.
        
        Args:
            story_type: One of "top", "new", "best"
            limit: Number of stories to fetch
            min_score: Minimum story score
        """
        try:
            # Validate story type
            valid_types = ["top", "new", "best"]
            if story_type not in valid_types:
                story_type = "top"
            
            # Use existing fetcher
            articles = await self.hackernews.fetch(
                max_articles=limit,
                story_type=story_type
            )
            
            # Filter by score if needed
            filtered = [a for a in articles if a.metadata.get("score", 0) >= min_score]
            
            content = []
            for article in filtered[:limit]:
                content.append({
                    "type": "text",
                    "text": f"**{article.title}**\n"
                           f"URL: {article.url}\n"
                           f"Score: {article.metadata.get('score', 0)}\n"
                           f"Comments: {article.metadata.get('comments', 0)}\n"
                           f"Posted: {article.published_at.isoformat()}"
                })
            
            return ToolResult(content=content)
            
        except Exception as e:
            return ToolResult(
                content=[{"type": "text", "text": f"Error fetching HackerNews: {str(e)}"}],
                is_error=True
            )
    
    async def get_rss_feed_articles(
        self,
        feed_names: Optional[List[str]] = None,
        limit: int = 20,
        hours_back: int = 24
    ) -> ToolResult:
        """
        Fetch articles from configured RSS feeds.
        
        Args:
            feed_names: Specific feed names to fetch from
            limit: Maximum articles to return
            hours_back: How many hours back to fetch
        """
        try:
            # Use existing RSS fetcher
            articles = await self.rss.fetch(max_articles=limit * 2)  # Fetch extra for filtering
            
            # Filter by time
            cutoff = datetime.utcnow() - timedelta(hours=hours_back)
            recent = [a for a in articles if a.published_at > cutoff]
            
            # Filter by feed names if specified
            if feed_names:
                recent = [a for a in recent if any(
                    name.lower() in a.metadata.get("feed_name", "").lower()
                    for name in feed_names
                )]
            
            content = []
            for article in recent[:limit]:
                content.append({
                    "type": "text",
                    "text": f"**{article.title}**\n"
                           f"Source: {article.metadata.get('feed_name', 'Unknown')}\n"
                           f"URL: {article.url}\n"
                           f"Summary: {article.content[:300]}...\n"
                           f"Published: {article.published_at.isoformat()}"
                })
            
            return ToolResult(content=content)
            
        except Exception as e:
            return ToolResult(
                content=[{"type": "text", "text": f"Error fetching RSS feeds: {str(e)}"}],
                is_error=True
            )

# Task 5: Analysis Tools
# src/mcp/tools/analysis.py
import asyncio
from typing import Optional, Dict, Any
from uuid import UUID

from src.repositories.articles import ArticleRepository
from src.agents.news_agent import NewsAnalyzer
from src.agents.digest_agent import DigestAgent
from src.services.deduplication import DeduplicationService
from src.config import get_settings
from supabase import create_client
from ..types import ToolResult

class AnalysisTools:
    """Analysis and summarization tools for MCP."""
    
    def __init__(self):
        """Initialize services and agents."""
        settings = get_settings()
        self.supabase = create_client(settings.supabase_url, settings.supabase_anon_key)
        self.article_repo = ArticleRepository(self.supabase)
        self.news_analyzer = NewsAnalyzer()
        self.digest_agent = DigestAgent()
        self.dedup_service = DeduplicationService(self.supabase)
    
    async def search_content(
        self,
        query: str,
        source: Optional[str] = None,
        limit: int = 10,
        min_relevance: Optional[int] = None
    ) -> ToolResult:
        """
        Search across all aggregated content.
        
        Args:
            query: Search query text
            source: Optional source filter (arxiv, hackernews, rss)
            limit: Maximum results
            min_relevance: Minimum relevance score filter
        """
        try:
            # Use repository search method
            articles, total = await self.article_repo.search_articles(
                query=query,
                source=source,
                limit=limit,
                offset=0
            )
            
            # Filter by relevance if specified
            if min_relevance:
                articles = [a for a in articles if a.relevance_score >= min_relevance]
            
            content = []
            content.append({
                "type": "text",
                "text": f"Found {len(articles)} results for '{query}' (total: {total})\n"
            })
            
            for article in articles:
                content.append({
                    "type": "text",
                    "text": f"**{article.title}**\n"
                           f"Source: {article.source.value}\n"
                           f"Relevance: {article.relevance_score}/100\n"
                           f"URL: {article.url}\n"
                           f"Summary: {article.summary or article.content[:200]}...\n"
                })
            
            return ToolResult(content=content)
            
        except Exception as e:
            return ToolResult(
                content=[{"type": "text", "text": f"Search failed: {str(e)}"}],
                is_error=True
            )
    
    async def summarize_article(
        self,
        article_id: Optional[str] = None,
        url: Optional[str] = None,
        content: Optional[str] = None
    ) -> ToolResult:
        """
        Generate AI summary of an article.
        
        Args:
            article_id: UUID of article in database
            url: URL of article to fetch and summarize
            content: Raw content to summarize
        """
        try:
            article = None
            
            # Get article from database if ID provided
            if article_id:
                article = await self.article_repo.get_article_by_id(UUID(article_id))
                if not article:
                    return ToolResult(
                        content=[{"type": "text", "text": f"Article {article_id} not found"}],
                        is_error=True
                    )
            
            # Create temporary article for analysis if content provided
            elif content:
                from src.models.articles import Article, ArticleSource
                article = Article(
                    source_id="temp",
                    source=ArticleSource.RSS,
                    title="User Provided Content",
                    content=content,
                    url=url or "https://example.com",
                    published_at=datetime.utcnow()
                )
            else:
                return ToolResult(
                    content=[{"type": "text", "text": "Must provide article_id or content"}],
                    is_error=True
                )
            
            # Use news analyzer to generate summary
            analysis = await self.news_analyzer.analyze_article(article)
            
            content_parts = []
            content_parts.append({
                "type": "text",
                "text": f"**Article Summary**\n\n"
                       f"Title: {article.title}\n"
                       f"Relevance Score: {analysis.relevance_score}/100\n\n"
                       f"**Summary:**\n{analysis.summary}\n\n"
                       f"**Key Points:**\n"
            })
            
            for point in analysis.key_points:
                content_parts.append({
                    "type": "text",
                    "text": f"• {point}\n"
                })
            
            content_parts.append({
                "type": "text",
                "text": f"\n**Categories:** {', '.join(analysis.categories)}\n"
                       f"**Reasoning:** {analysis.reasoning}"
            })
            
            return ToolResult(content=content_parts)
            
        except Exception as e:
            return ToolResult(
                content=[{"type": "text", "text": f"Summarization failed: {str(e)}"}],
                is_error=True
            )
    
    async def generate_daily_digest(
        self,
        date: Optional[str] = None,
        min_relevance: int = 70,
        max_articles: int = 10
    ) -> ToolResult:
        """
        Generate a daily digest of top AI/ML news.
        
        Args:
            date: Date for digest (YYYY-MM-DD), defaults to today
            min_relevance: Minimum relevance score
            max_articles: Maximum articles to include
        """
        try:
            # Get top articles for digest
            since_hours = 24 if not date else 48  # Wider range if specific date
            
            top_articles = await self.article_repo.get_top_articles_for_digest(
                since_hours=since_hours,
                min_relevance_score=min_relevance,
                limit=max_articles
            )
            
            if not top_articles:
                return ToolResult(
                    content=[{"type": "text", "text": "No articles found for digest"}],
                    is_error=True
                )
            
            # Generate digest using agent
            digest_date = date or datetime.utcnow().strftime("%Y-%m-%d")
            digest = await self.digest_agent.generate_digest(
                articles=top_articles,
                digest_date=digest_date,
                max_summary_length=2000
            )
            
            content = []
            content.append({
                "type": "text",
                "text": f"**AI Daily Digest - {digest_date}**\n\n"
                       f"{digest.summary_text}\n\n"
                       f"**Top Stories:**\n"
            })
            
            for i, article in enumerate(top_articles[:5], 1):
                content.append({
                    "type": "text",
                    "text": f"\n{i}. **{article.title}**\n"
                           f"   Source: {article.source.value} | "
                           f"   Relevance: {article.relevance_score}/100\n"
                           f"   {article.summary or article.content[:200]}...\n"
                           f"   URL: {article.url}\n"
                })
            
            return ToolResult(content=content)
            
        except Exception as e:
            return ToolResult(
                content=[{"type": "text", "text": f"Digest generation failed: {str(e)}"}],
                is_error=True
            )

# Task 8: Main MCP Server
# src/mcp/server.py
import asyncio
import json
import sys
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from .types import MCPRequest, MCPResponse, ToolDefinition, ToolCallParams, ServerCapabilities
from .tools.content import ContentTools
from .tools.analysis import AnalysisTools
from .handlers import RequestHandler
from .errors import MCPError, ErrorCode

logger = logging.getLogger(__name__)

class MCPServer:
    """Model Context Protocol server for AI News Aggregator."""
    
    def __init__(self):
        """Initialize MCP server with tools."""
        self.content_tools = ContentTools()
        self.analysis_tools = AnalysisTools()
        self.handler = RequestHandler(self)
        self.tools = self._register_tools()
        
        logger.info("MCP Server initialized with %d tools", len(self.tools))
    
    def _register_tools(self) -> Dict[str, ToolDefinition]:
        """Register all available tools."""
        tools = {
            "get_latest_arxiv_papers": ToolDefinition(
                name="get_latest_arxiv_papers",
                description="Fetch recent AI/ML papers from ArXiv",
                input_schema={
                    "type": "object",
                    "properties": {
                        "categories": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "ArXiv categories to search"
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "Maximum papers to return",
                            "default": 10
                        },
                        "days_back": {
                            "type": "integer",
                            "description": "How many days back to search",
                            "default": 7
                        }
                    }
                }
            ),
            "get_hackernews_stories": ToolDefinition(
                name="get_hackernews_stories",
                description="Fetch top HackerNews stories about AI/ML",
                input_schema={
                    "type": "object",
                    "properties": {
                        "story_type": {
                            "type": "string",
                            "enum": ["top", "new", "best"],
                            "default": "top"
                        },
                        "limit": {
                            "type": "integer",
                            "default": 10
                        },
                        "min_score": {
                            "type": "integer",
                            "description": "Minimum story score",
                            "default": 50
                        }
                    }
                }
            ),
            "get_rss_feed_articles": ToolDefinition(
                name="get_rss_feed_articles",
                description="Fetch articles from configured RSS feeds",
                input_schema={
                    "type": "object",
                    "properties": {
                        "feed_names": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Specific feed names to fetch"
                        },
                        "limit": {
                            "type": "integer",
                            "default": 20
                        },
                        "hours_back": {
                            "type": "integer",
                            "default": 24
                        }
                    }
                }
            ),
            "search_content": ToolDefinition(
                name="search_content",
                description="Search across all aggregated AI/ML content",
                input_schema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query"
                        },
                        "source": {
                            "type": "string",
                            "enum": ["arxiv", "hackernews", "rss"],
                            "description": "Optional source filter"
                        },
                        "limit": {
                            "type": "integer",
                            "default": 10
                        },
                        "min_relevance": {
                            "type": "integer",
                            "description": "Minimum relevance score (0-100)"
                        }
                    },
                    "required": ["query"]
                }
            ),
            "summarize_article": ToolDefinition(
                name="summarize_article",
                description="Generate AI summary of an article",
                input_schema={
                    "type": "object",
                    "properties": {
                        "article_id": {
                            "type": "string",
                            "description": "UUID of article in database"
                        },
                        "url": {
                            "type": "string",
                            "description": "URL of article to summarize"
                        },
                        "content": {
                            "type": "string",
                            "description": "Raw content to summarize"
                        }
                    }
                }
            ),
            "generate_daily_digest": ToolDefinition(
                name="generate_daily_digest",
                description="Generate a daily digest of top AI/ML news",
                input_schema={
                    "type": "object",
                    "properties": {
                        "date": {
                            "type": "string",
                            "description": "Date for digest (YYYY-MM-DD)"
                        },
                        "min_relevance": {
                            "type": "integer",
                            "default": 70
                        },
                        "max_articles": {
                            "type": "integer",
                            "default": 10
                        }
                    }
                }
            )
        }
        
        return tools
    
    async def execute_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        """Execute a tool by name with arguments."""
        # Map tool names to methods
        tool_map = {
            "get_latest_arxiv_papers": self.content_tools.get_latest_arxiv_papers,
            "get_hackernews_stories": self.content_tools.get_hackernews_stories,
            "get_rss_feed_articles": self.content_tools.get_rss_feed_articles,
            "search_content": self.analysis_tools.search_content,
            "summarize_article": self.analysis_tools.summarize_article,
            "generate_daily_digest": self.analysis_tools.generate_daily_digest,
        }
        
        if name not in tool_map:
            raise MCPError(ErrorCode.METHOD_NOT_FOUND, f"Tool '{name}' not found")
        
        # Execute tool
        result = await tool_map[name](**arguments)
        return result
    
    async def handle_request(self, request_data: str) -> str:
        """Handle incoming JSON-RPC request."""
        try:
            # Parse request
            request_dict = json.loads(request_data)
            request = MCPRequest(**request_dict)
            
            # Route to handler
            result = await self.handler.handle(request)
            
            # Create response
            response = MCPResponse(
                jsonrpc="2.0",
                result=result,
                id=request.id
            )
            
        except json.JSONDecodeError as e:
            response = MCPResponse(
                jsonrpc="2.0",
                error={
                    "code": ErrorCode.PARSE_ERROR,
                    "message": "Parse error",
                    "data": str(e)
                }
            )
        except MCPError as e:
            response = MCPResponse(
                jsonrpc="2.0",
                error={
                    "code": e.code,
                    "message": e.message,
                    "data": e.data
                },
                id=request.id if 'request' in locals() else None
            )
        except Exception as e:
            logger.error("Unexpected error: %s", e, exc_info=True)
            response = MCPResponse(
                jsonrpc="2.0",
                error={
                    "code": ErrorCode.INTERNAL_ERROR,
                    "message": "Internal error",
                    "data": str(e)
                },
                id=request.id if 'request' in locals() else None
            )
        
        return response.model_dump_json()
    
    async def run(self):
        """Run MCP server on stdio."""
        logger.info("MCP Server starting on stdio")
        
        reader = asyncio.StreamReader()
        protocol = asyncio.StreamReaderProtocol(reader)
        await asyncio.get_event_loop().connect_read_pipe(lambda: protocol, sys.stdin)
        
        writer = sys.stdout
        
        while True:
            try:
                # Read line from stdin
                line = await reader.readline()
                if not line:
                    break
                
                # Decode and handle request
                request_data = line.decode('utf-8').strip()
                if not request_data:
                    continue
                
                logger.debug("Received request: %s", request_data[:100])
                
                # Process request
                response = await self.handle_request(request_data)
                
                # Write response to stdout
                writer.write(response.encode('utf-8'))
                writer.write(b'\n')
                writer.flush()
                
                logger.debug("Sent response: %s", response[:100])
                
            except KeyboardInterrupt:
                logger.info("Server interrupted by user")
                break
            except Exception as e:
                logger.error("Error in main loop: %s", e, exc_info=True)
                # Continue running despite errors

# Task 9: Server Entry Point
# src/mcp_main.py
#!/usr/bin/env python
"""
MCP Server entry point for AI News Aggregator.

This starts the MCP server that exposes tools to AI assistants.
"""

import asyncio
import logging
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.mcp.server import MCPServer
from src.config import get_settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stderr)  # Log to stderr to keep stdout clean
    ]
)

logger = logging.getLogger(__name__)

async def main():
    """Main entry point for MCP server."""
    try:
        # Load settings
        settings = get_settings()
        logger.info("Starting AI News Aggregator MCP Server")
        
        # Validate required environment variables
        if not settings.supabase_url or not settings.supabase_anon_key:
            logger.error("Missing required environment variables (SUPABASE_URL, SUPABASE_ANON_KEY)")
            sys.exit(1)
        
        # Create and run server
        server = MCPServer()
        await server.run()
        
    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
    except Exception as e:
        logger.error("Fatal error: %s", e, exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
```

### Integration Points
```yaml
ENVIRONMENT:
  - share: Same .env file as backend
  - required: SUPABASE_URL, SUPABASE_ANON_KEY
  - optional: GEMINI_API_KEY (for summarization)
  
DEPENDENCIES:
  - add to: requirements.txt
  - package: mcp
  - existing: All backend dependencies already installed
  
BACKEND INTEGRATION:
  - import: Direct Python imports from src/
  - no HTTP: Don't use localhost API calls
  - shared: Database connections, services, agents
  
CLAUDE CONFIG:
  - file: claude_mcp_config.json
  - command: python src/mcp_main.py
  - env: Pass through required variables
```

## Validation Loop

### Level 1: Syntax & Style
```bash
cd /Users/peterbrown/Documents/Code/ai-news-aggregator-agent
source venv_linux/bin/activate

# Check syntax
ruff check src/mcp/ --fix
mypy src/mcp/

# Expected: No errors
```

### Level 2: Unit Tests
```python
# CREATE tests/test_mcp/test_tools.py
import pytest
from unittest.mock import Mock, AsyncMock
from src.mcp.tools.content import ContentTools
from src.mcp.types import ToolResult

@pytest.mark.asyncio
async def test_get_arxiv_papers():
    """Test ArXiv paper fetching."""
    tools = ContentTools()
    
    # Mock the fetcher
    mock_articles = [Mock(
        title="Test Paper",
        author="Test Author",
        url="https://arxiv.org/test",
        content="Test content",
        published_at=datetime.utcnow()
    )]
    
    tools.arxiv.fetch = AsyncMock(return_value=mock_articles)
    
    result = await tools.get_latest_arxiv_papers(max_results=1)
    
    assert isinstance(result, ToolResult)
    assert not result.is_error
    assert len(result.content) == 1
    assert "Test Paper" in result.content[0]["text"]

@pytest.mark.asyncio
async def test_search_content():
    """Test content search."""
    from src.mcp.tools.analysis import AnalysisTools
    
    tools = AnalysisTools()
    
    # Mock repository
    mock_articles = [Mock(
        title="ML Article",
        source=Mock(value="arxiv"),
        relevance_score=95,
        url="https://test.com",
        summary="Test summary"
    )]
    
    tools.article_repo.search_articles = AsyncMock(return_value=(mock_articles, 1))
    
    result = await tools.search_content("machine learning", limit=1)
    
    assert isinstance(result, ToolResult)
    assert not result.is_error
    assert "ML Article" in str(result.content)

# Run tests
pytest tests/test_mcp/ -v
```

### Level 3: MCP Protocol Tests
```python
# CREATE tests/test_mcp/test_protocol.py
import json
import pytest
from src.mcp.server import MCPServer

@pytest.mark.asyncio
async def test_tools_list():
    """Test tools/list request."""
    server = MCPServer()
    
    request = json.dumps({
        "jsonrpc": "2.0",
        "method": "tools/list",
        "id": 1
    })
    
    response = await server.handle_request(request)
    response_data = json.loads(response)
    
    assert response_data["jsonrpc"] == "2.0"
    assert "result" in response_data
    assert "tools" in response_data["result"]
    assert len(response_data["result"]["tools"]) == 6

@pytest.mark.asyncio
async def test_tool_call():
    """Test tools/call request."""
    server = MCPServer()
    
    # Mock the tool
    server.content_tools.get_hackernews_stories = AsyncMock(
        return_value=Mock(content=[{"type": "text", "text": "Test story"}])
    )
    
    request = json.dumps({
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": "get_hackernews_stories",
            "arguments": {"limit": 1}
        },
        "id": 2
    })
    
    response = await server.handle_request(request)
    response_data = json.loads(response)
    
    assert response_data["jsonrpc"] == "2.0"
    assert "result" in response_data
    assert response_data["id"] == 2

@pytest.mark.asyncio
async def test_invalid_method():
    """Test invalid method handling."""
    server = MCPServer()
    
    request = json.dumps({
        "jsonrpc": "2.0",
        "method": "invalid/method",
        "id": 3
    })
    
    response = await server.handle_request(request)
    response_data = json.loads(response)
    
    assert "error" in response_data
    assert response_data["error"]["code"] == -32601  # Method not found
```

### Level 4: Integration Test with Claude
```bash
# Create Claude configuration
cat > ~/Library/Application\ Support/Claude/claude_desktop_config.json << 'EOF'
{
  "mcpServers": {
    "ai-news-aggregator": {
      "command": "python",
      "args": ["/Users/peterbrown/Documents/Code/ai-news-aggregator-agent/src/mcp_main.py"],
      "env": {
        "SUPABASE_URL": "${SUPABASE_URL}",
        "SUPABASE_ANON_KEY": "${SUPABASE_ANON_KEY}",
        "GEMINI_API_KEY": "${GEMINI_API_KEY}"
      }
    }
  }
}
EOF

# Restart Claude Desktop
# Test by asking Claude: "Can you search for recent transformer papers?"
```

### Level 5: Rate Limit Verification
```python
# CREATE tests/test_mcp/test_rate_limits.py
import time
import pytest
from src.mcp.tools.content import ContentTools

@pytest.mark.asyncio
async def test_arxiv_rate_limit():
    """Verify ArXiv 3-second rate limit is respected."""
    tools = ContentTools()
    
    # Time two consecutive calls
    start = time.time()
    
    # First call
    await tools.get_latest_arxiv_papers(max_results=1)
    
    # Second call
    await tools.get_latest_arxiv_papers(max_results=1)
    
    elapsed = time.time() - start
    
    # Should take at least 3 seconds due to rate limit
    assert elapsed >= 3.0, f"Rate limit not respected: {elapsed}s"
```

## MCP Validation Commands
```yaml
# Use Supabase MCP to verify data access
mcp__supabase__execute_sql:
  query: |
    SELECT COUNT(*) as article_count
    FROM articles
    WHERE created_at > NOW() - INTERVAL '24 hours';
# Expected: Recent article count

# Test search functionality via database
mcp__supabase__execute_sql:
  query: |
    SELECT title, source, relevance_score
    FROM articles
    WHERE title ILIKE '%transformer%'
    LIMIT 5;
# Expected: Articles matching search term
```

## Final Validation Checklist
- [ ] All 14 tasks completed successfully
- [ ] MCP Python SDK installed
- [ ] 6 MVP tools implemented and tested
- [ ] JSON-RPC 2.0 protocol compliance
- [ ] Rate limits respected (ArXiv 3s verified)
- [ ] Search returns results < 500ms
- [ ] Summarization uses existing agents
- [ ] Error handling with proper codes
- [ ] All unit tests pass
- [ ] Protocol tests pass
- [ ] Claude Desktop integration works
- [ ] No duplicate backend logic (direct imports)
- [ ] Logging to stderr (stdout clean for MCP)
- [ ] Environment variables validated

---

## Anti-Patterns to Avoid
- ❌ Don't make HTTP calls to backend - use direct imports
- ❌ Don't bypass ArXiv 3-second rate limit
- ❌ Don't log to stdout - use stderr only
- ❌ Don't use camelCase tool names - use snake_case
- ❌ Don't create new database connections - reuse backend
- ❌ Don't implement sync tools - all must be async
- ❌ Don't skip JSON-RPC format validation
- ❌ Don't hardcode credentials - use environment

## Performance Notes
1. **Direct Imports**: Zero network overhead by importing backend
2. **Rate Limiting**: Inherited from backend fetchers automatically
3. **Async Everything**: Non-blocking tool execution
4. **Connection Pooling**: Reuse Supabase client from backend
5. **Caching**: Leverage existing backend caches

## MCP Tool Usage
- **Context7**: Get MCP Python SDK documentation
- **Supabase**: Verify database queries work correctly
- **IDE Diagnostics**: Type checking and validation

## Score: 9/10
High confidence due to:
- Existing backend provides all functionality
- Clear MCP specification to follow
- Direct service imports (no reimplementation)
- Comprehensive test coverage included
- Rate limiting already handled in backend

The 1-point deduction is for potential complexity in Claude Desktop configuration and environment variable passing.