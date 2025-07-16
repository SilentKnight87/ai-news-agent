## FEATURE:

- AI-powered news aggregator that monitors multiple AI/ML news sources and research papers
- PydanticAI agents for intelligent article summarization and relevance scoring
- Semantic deduplication using vector embeddings to prevent duplicate stories
- Daily digest generation with ElevenLabs text-to-speech for audio summaries
- Real-time web dashboard with Supabase backend and Next.js frontend
- Automated data pipeline that fetches from ArXiv, HackerNews, and RSS feeds
- Scheduled processing via Supabase Edge Functions for continuous updates

## DATA SOURCE TIERS:

### MVP Data Sources (Implement First - Week 1-2):
1. **ArXiv API** (FREE)
   - Categories: cs.AI, cs.LG, cs.CL
   - Update frequency: Every 30 minutes
   - Rate limit: 1 request per 3 seconds
   - Implementation: Direct API calls, no auth required

2. **HackerNews API** (FREE)
   - Filter: AI/ML tagged stories, top stories mentioning AI keywords
   - Update frequency: Every 15 minutes
   - Implementation: Firebase API, fetch story IDs then individual stories
   - No authentication required

3. **RSS Feed Bundle** (FREE)
   - Sources: OpenAI Blog, Anthropic Blog, Google AI Blog, Hugging Face Blog
   - Update frequency: Every hour
   - Implementation: feedparser library, simple HTTP requests

### Tier 1: Primary Sources (Month 2-3 Implementation):
**AI Research & Labs:**
- Papers with Code (RSS + web scraping)
- Meta AI Research Blog (RSS)
- DeepMind Blog (RSS)
- Microsoft Research AI (RSS)
- MIT CSAIL News (RSS)

**Tech News Sites:**
- TechCrunch AI section (RSS + API if available)
- The Verge AI section (RSS)
- VentureBeat AI (RSS)
- MIT Technology Review AI (RSS)
- IEEE Spectrum AI (RSS)
- The Information AI (requires subscription - web scraping)

**Industry Blogs:**
- AWS Machine Learning Blog (RSS)
- Google Cloud AI Blog (RSS)
- Weights & Biases Blog (RSS)
- Neptune.ai Blog (RSS)
- Towards Data Science (Medium API)

### Tier 2: Community Sources (Month 3-4 Implementation):
**Reddit Communities:**
- r/MachineLearning (Reddit API - note: paid API)
- r/LocalLLaMA
- r/singularity
- r/OpenAI
- r/artificial
- r/deeplearning
- Implementation: PRAW library, requires API credentials and payment

**YouTube Channels:**
- Two Minute Papers
- Yannic Kilcher
- AI Explained
- Matthew Berman
- David Shapiro
- Implementation: YouTube Data API v3 (quota limits apply)

**Developer Communities:**
- dev.to AI/ML tags (API available)
- Hacker Noon AI section (RSS)
- Twitter/X Lists (requires API access - expensive)
- LinkedIn AI content (complex scraping, consider LinkedIn API)

**Forums & Discussions:**
- LessWrong AI posts (RSS)
- AI Alignment Forum (RSS)
- ML Subreddit Wiki updates

### Implementation Priority Notes:
- **MVP Focus**: Get ArXiv + HackerNews + RSS working perfectly before adding more
- **Deduplication**: More sources = more duplicates. Solid vector similarity required before Tier 1
- **Cost Consideration**: Reddit API now costs money, YouTube has strict quotas
- **Legal**: Some sources may require permission for commercial use
- **Maintenance**: Each source needs error handling and monitoring

## EXAMPLES:

In the `examples/` folder, create the following examples to demonstrate core functionality:

- `examples/agents/news_agent.py` - PydanticAI agent for article summarization with structured output (title, summary, key_points, relevance_score)
- `examples/agents/digest_agent.py` - Agent that creates daily digest from top articles
- `examples/fetchers/arxiv_fetcher.py` - Example of fetching papers from ArXiv API with rate limiting
- `examples/fetchers/hackernews_fetcher.py` - HackerNews Firebase API integration
- `examples/fetchers/rss_fetcher.py` - Generic RSS feed fetcher for blogs
- `examples/fetchers/reddit_fetcher.py` - Reddit API integration example (for future Tier 2)
- `examples/fetchers/youtube_fetcher.py` - YouTube Data API example (for future Tier 2)
- `examples/deduplication/vector_similarity.py` - Demonstration of using embeddings for duplicate detection
- `examples/supabase/schema.sql` - Database schema with pgvector extension
- `examples/frontend/article_card.tsx` - React component for displaying articles

## DOCUMENTATION:

- PydanticAI documentation: https://ai.pydantic.dev/
- Supabase documentation: https://supabase.com/docs
- Supabase Vector/pgvector guide: https://supabase.com/docs/guides/ai/vector-embeddings
- Google Gemini API: https://ai.google.dev/gemini-api/docs
- ArXiv API documentation: https://info.arxiv.org/help/api/index.html
- HackerNews API: https://github.com/HackerNews/API
- ElevenLabs API: https://elevenlabs.io/docs/api-reference/text-to-speech
- Reddit API (Tier 2): https://www.reddit.com/dev/api/
- YouTube Data API v3 (Tier 2): https://developers.google.com/youtube/v3
- RSS Feed Specification: https://www.rssboard.org/rss-specification
- Papers with Code API: https://paperswithcode.com/api/v1/docs/
- Medium API (Tier 1): https://github.com/Medium/medium-api-docs
- Next.js documentation: https://nextjs.org/docs
- Vercel deployment guide: https://vercel.com/docs

## OTHER CONSIDERATIONS:

- **Rate Limiting**: 
  - ArXiv: 3-second delays between requests (strict requirement)
  - HackerNews: No official limits but be respectful (suggest 1 req/sec)
  - Reddit API: 60 requests per minute (requires OAuth)
  - YouTube API: 10,000 quota units per day (search costs 100 units)
  - RSS feeds: Respect cache headers, typically update every 15-60 minutes
  - Implement exponential backoff for all sources
- **Embedding Models**: Use HuggingFace's free inference API (all-MiniLM-L6-v2) for embeddings to keep costs down. Cache embeddings to avoid re-processing.
- **Deduplication Threshold**: 85% similarity threshold works well for news articles. Store both exact URL matching and semantic similarity.
- **Gemini Free Tier**: Limited to 60 requests per minute. Batch process articles and use caching strategically.
- **Supabase Edge Functions**: Use Deno runtime. Remember to handle CORS for frontend integration.
- **Environment Variables**: Include comprehensive .env.example with all required keys (SUPABASE_URL, SUPABASE_ANON_KEY, GEMINI_API_KEY, ELEVENLABS_API_KEY, HF_API_KEY)
- **Database Migrations**: Use Supabase CLI for version-controlled migrations
- **Vector Index**: Create IVFFlat index after ~1000 articles for better performance
- **Audio Generation**: Limit daily digest to 2000 characters to control ElevenLabs costs
- **Error Handling**: Implement circuit breakers for external APIs to prevent cascade failures
- **Monitoring**: Use Supabase built-in logging and consider adding Sentry for production
- **Testing**: Mock external APIs in tests. Provide sample responses for each data source.
- **Project Structure**: Follow a clear separation between data fetching, processing, and presentation layers
- **Type Safety**: Leverage PydanticAI's type validation for all API responses and data models
- **Deployment**: Start with Vercel for frontend (free tier), Supabase for backend (free tier covers MVP needs)
- **Data Source Costs**: 
  - MVP sources: All free (ArXiv, HackerNews, RSS)
  - Tier 1: Mostly free via RSS, some may require subscriptions (The Information)
  - Tier 2: Reddit API ~$0.24/1000 requests, YouTube free but limited quota, Twitter/X expensive
  - Budget $50-100/month for Tier 2 data sources when scaling
- **Source Reliability**: Implement health checks for each source. Auto-disable sources that fail repeatedly to prevent pipeline blockage.
- **Content Rights**: Add source attribution to all content. Some sources may restrict commercial use - review terms of service.
- **Incremental Implementation**: Each new source should be implemented as a separate module with its own error handling and monitoring