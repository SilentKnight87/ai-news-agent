## FEATURE:

- Model Context Protocol (MCP) server that exposes AI News Aggregator data and tools to AI assistants
- Direct integration with Claude, Cursor, and other MCP-compatible clients
- Real-time access to curated AI/ML news content, summaries, and analytics
- Content retrieval tools for ArXiv papers, HackerNews stories, and RSS feeds
- AI-powered analysis tools for summarization, trend analysis, and insights extraction
- Export and reporting capabilities in multiple formats (JSON, CSV, PDF, Markdown)
- Configuration management for RSS feeds, preferences, and analytics
- Leverages existing backend infrastructure for data access and processing

## MCP TOOL TIERS:

### MVP Tools (Implement First - Week 1-2):
1. **Content Retrieval Tools** (FREE - uses existing backend)
   - get_latest_arxiv_papers: Fetch recent AI/ML papers with filtering
   - get_hackernews_stories: Retrieve top HN stories related to AI
   - get_rss_feed_articles: Pull articles from configured feeds
   - search_content: Search across all content sources
   - Rate limit: Inherits backend rate limiting (3 sec ArXiv, 1 req/sec HN)
   - Implementation: Direct calls to existing backend services

2. **Basic Analysis Tools** (Uses existing AI agents)
   - summarize_article: Generate AI summaries using existing PydanticAI agents
   - generate_daily_digest: Create curated daily digest from backend data
   - extract_key_insights: Pull actionable insights from articles
   - Implementation: Leverage existing Gemini integration and analysis pipeline

### Tier 1: Advanced Tools (Month 2-3 Implementation):
**Export & Reporting:**
- export_articles: Export in JSON, CSV, Markdown, PDF formats
- generate_report: Weekly/monthly/topic-based comprehensive reports
- Integration with existing TTS for audio report generation

**Analytics & Trends:**
- analyze_trends: Identify trending topics using vector similarity
- get_analytics: Usage stats, content metrics, source performance
- trend_visualization: Generate charts and graphs for insights

### Tier 2: Configuration & Management (Month 3-4 Implementation):
**Feed Management:**
- manage_rss_feeds: Add/remove/update RSS sources dynamically
- set_preferences: Configure user-specific filters and settings
- source_health_monitoring: Check status of all data sources

**Advanced Features:**
- generate_podcast_script: Create audio-ready scripts from articles
- real_time_notifications: WebSocket integration for live updates
- collaborative_features: Shared digests and team preferences

### Implementation Priority Notes:
- **MVP Focus**: Get core content retrieval working with existing backend first
- **Reuse Existing**: Leverage all existing backend services, don't duplicate logic
- **MCP Standards**: Follow MCP protocol specifications for tool definitions
- **Error Handling**: Inherit robust error handling from existing backend
- **Authentication**: Use existing environment variable patterns

## EXAMPLES:

In the `examples/` folder, create the following examples to demonstrate MCP functionality:

- `examples/mcp-client/claude_integration.py` - Example of using MCP tools with Claude
- `examples/mcp-client/cursor_workflow.py` - Cursor IDE integration examples
- `examples/mcp-tools/content_retrieval.py` - Demonstrate content fetching tools
- `examples/mcp-tools/analysis_workflow.py` - AI analysis and summarization examples
- `examples/mcp-tools/export_examples.py` - Various export format demonstrations
- `examples/mcp-tools/trend_analysis.py` - Trending topic identification
- `examples/mcp-server/server_setup.py` - MCP server configuration and startup
- `examples/mcp-server/tool_registration.py` - How to register new MCP tools

## DOCUMENTATION:

- Model Context Protocol (MCP) specification: https://spec.modelcontextprotocol.io/
- MCP Python SDK: https://github.com/modelcontextprotocol/python-sdk
- Claude MCP integration guide: https://docs.anthropic.com/en/docs/build-with-claude/mcp
- Cursor MCP documentation: https://docs.cursor.com/integrations/mcp
- Existing backend API documentation: http://localhost:8000/docs (when running)
- PydanticAI documentation: https://ai.pydantic.dev/
- Supabase documentation: https://supabase.com/docs
- FastAPI async patterns: https://fastapi.tiangolo.com/async/
- Python asyncio documentation: https://docs.python.org/3/library/asyncio.html

## OTHER CONSIDERATIONS:

- **MCP Protocol Compliance**: 
  - Follow MCP specification for tool definitions and responses
  - Use proper JSON-RPC 2.0 format for all communications
  - Implement required server capabilities (tools, resources)
  - Handle MCP client initialization and lifecycle properly
- **Backend Integration**: Reuse existing backend services via direct Python imports, don't duplicate HTTP calls
- **Error Handling**: Inherit circuit breaker patterns from existing backend, propagate errors properly to MCP clients
- **Rate Limiting**: Respect existing backend rate limits, don't bypass ArXiv 3-second delays or HN throttling
- **Data Consistency**: Use same Supabase connection pool and database models as backend
- **Environment Variables**: Use same .env patterns as backend, share configuration where possible
- **Async Patterns**: All MCP tools must be async, use existing async patterns from backend services
- **Testing**: Mock MCP client interactions, reuse existing backend test fixtures and patterns
- **Project Structure**: Keep MCP server code separate but import shared utilities from backend/shared
- **Type Safety**: Leverage existing Pydantic models from backend, extend for MCP-specific responses
- **Deployment**: MCP server can run alongside backend API or as separate process, use same Docker patterns
- **Tool Registration**: Follow MCP dynamic tool registration if tools need to be enabled/disabled
- **Security**: Validate all MCP client inputs, use existing backend authentication patterns
- **Performance**: Cache frequent database queries, use existing embedding cache from backend
- **Monitoring**: Integrate with existing logging and monitoring systems from backend
- **Client Compatibility**: Test with Claude, Cursor, and other major MCP clients
- **Version Management**: Keep MCP server version in sync with backend API versions