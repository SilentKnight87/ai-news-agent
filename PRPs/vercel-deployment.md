# Problem Resolution Plan: Vercel Deployment Implementation

name: "Vercel Deployment PRP - FastAPI Backend + Next.js Frontend (Fluid Compute)"
description: |

## Purpose
Comprehensive implementation guide for deploying the AI News Aggregator to Vercel using Vercel Fluid Compute for the FastAPI backend and standard hosting for the Next.js frontend, enabling a fully managed, scalable, and cost-effective production deployment with 85% cost savings.

## Core Principles
1. **Fluid Compute First**: Leverage Vercel Fluid Compute for cost optimization and extended execution duration
2. **Connection Pooling Preservation**: Maintain existing database connection patterns
3. **Security & Performance**: Follow Vercel best practices for production deployments
4. **Simplified Architecture**: Single entry point deployment with minimal configuration
5. **Cost Optimization**: Leverage 85% cost savings and generous free tier limits

---

## Goal
Deploy a production-ready AI News Aggregator to Vercel with:
- FastAPI backend running on Vercel Fluid Compute (extended duration, instance reuse)
- Next.js frontend with optimized API proxying
- Secure environment variable management
- Preserved database connection pooling for Supabase
- Monitoring and error tracking
- Cost-effective scaling with 85% cost savings

## Why
- **Cost Efficiency**: Vercel Fluid Compute offers 85-90% cost savings on AI workloads with generous free tier
- **Reduced Cold Starts**: Fluid Compute reduces cold start impact; validate in metrics
- **Unified Platform**: Single deployment pipeline for both frontend and backend
- **Auto Scaling**: Built-in scaling without infrastructure management
- **Production Ready**: Existing codebase is 100% complete and needs deployment

## What
Transform the current local FastAPI + Next.js application into a fully deployed Vercel application with:

### Success Criteria
- [ ] Backend API deployed as Vercel Fluid Compute and responding to requests
- [ ] Frontend deployed and calling backend APIs via NEXT_PUBLIC_API_BASE_URL with CORS passing
- [ ] All 14 API endpoints functioning in production
- [ ] Database connections working with preserved pooling
- [ ] MCP server updated to use production URLs
- [ ] Environment variables securely configured
- [ ] Audio streaming and TTS pipeline operational
- [ ] Performance monitoring active
- [ ] Cost usage optimized with Fluid Compute (85% savings)

## All Needed Context

### Documentation & References
```yaml
# MUST READ - Include these in your context window
- url: https://vercel.com/docs/functions/serverless-functions/runtimes/python
  why: Official Vercel Python runtime documentation and limitations
  
- url: https://vercel.com/docs/functions/serverless-functions
  why: Vercel Serverless Functions overview
  critical: Python runtime behavior, limits, routing

- url: https://vercel.com/docs/projects/project-configuration#rewrites
  why: vercel.json rewrites are path-to-path (no file extensions)
  critical: Route /api/v1/* to /api/index

- url: https://vercel.com/docs/projects/monorepos
  why: Configure two Vercel projects from one repo (UI and API)

- file: /spec/vercel-deployment.md
  why: Original deployment specification with architecture diagrams
  
- file: /src/main.py
  why: Current FastAPI application structure and startup/shutdown handlers
  
- file: /UI/next.config.ts
  why: Current Next.js configuration that needs API proxying setup

- doc: https://vercel.com/docs/concepts/functions/serverless-functions/environment-variables
  section: Environment variable management and security
  critical: Secure storage of API keys and database credentials

- docfile: /PRPs/completed/audio-integration.md
  why: Audio pipeline architecture that must work in serverless environment
```

### Current Codebase Tree
```bash
ai-news-aggregator-agent/
├── src/                     # FastAPI backend (needs restructuring)
│   ├── main.py             # FastAPI app with lifespan handlers
│   ├── api/                # API routes and dependencies
│   ├── agents/             # PydanticAI news and digest agents
│   ├── services/           # TTS, embeddings, scheduler, rate limiter
│   ├── repositories/       # Database access layer
│   ├── models/             # Pydantic models and database schemas
│   └── tasks/              # Background tasks and audio processing
├── UI/                     # Next.js frontend (needs proxy config)
│   ├── src/app/            # App router structure
│   ├── src/components/     # React components
│   ├── src/hooks/          # Custom hooks for API calls
│   └── next.config.ts      # Next.js configuration
├── requirements.txt        # Python dependencies (ensure 'cachetools' present)
├── mcp-server/            # Deployed MCP server (needs URL updates)
└── spec/vercel-deployment.md # Original deployment specification
```

### Desired Codebase Tree
```bash
ai-news-aggregator-agent/
├── api/                    # NEW: Vercel Fluid Compute directory (backend project root)
│   └── index.py           # Single FastAPI ASGI entrypoint (no adapter)
├── src/                   # UNCHANGED: Core business logic preserved
├── UI/                    # Frontend project (separate Vercel project)
│   ├── next.config.ts     # Minimal config; uses env API_BASE_URL
│   └── src/lib/api.ts     # Centralized API base URL (relative in dev, absolute in prod)
├── vercel.json            # Backend: Python function configuration + rewrites
├── requirements.txt       # UPDATED: Lean, no Mangum
└── README.md             # UPDATED: Monorepo deployment instructions (two Vercel projects)
```

### Monorepo Deployment Setup
- Projects:
  - Backend project root = repository root (includes [vercel.json](vercel.json)), deploys Python FastAPI under Fluid Compute
  - Frontend project root = [UI/](UI/next.config.ts) (Next.js), separate Vercel project
- Environment variables:
  - Backend: set variables listed in “Task 4.2: Environment Variable Migration (BACKEND)”
  - Frontend: set NEXT_PUBLIC_API_BASE_URL to backend domain and NEXT_PUBLIC_SUPABASE_* as needed
- Domains:
  - Backend e.g., https://your-backend.vercel.app
  - Frontend e.g., https://your-ui.vercel.app
- CORS:
  - Ensure [cors_allowed_origins](src/config.py:57) includes the frontend domain (comma-separated)
- Routing:
  - Frontend calls backend via absolute URL in production (no cross-project rewrites)
  - Backend maps /api/v1/* to the function entry via vercel.json rewrites

### Known Gotchas & Library Quirks
```python
# CRITICAL: Vercel Fluid Compute notes
# - ~50MB deployment size limit (including dependencies)
# - Up to 300s execution time
# - Instance reuse possible; do not assume parallel concurrency within a single instance
# - Connection pooling preserved per warm instance

# CRITICAL: Vercel Python runtime (ASGI)
# - Expose FastAPI app directly (no AWS/Lambda adapters)
# - Avoid long-lived background schedulers; use Vercel Cron or Supabase cron
# - Lifespan runs per instance; design startup to be idempotent

# CRITICAL: Database connection pooling
# - SQLAlchemy connection pools work normally in Fluid Compute
# - Existing connection patterns can be preserved
# - Supabase client connection pooling maintained

# CRITICAL: Environment variables
# - Production secrets must be in Vercel dashboard
# - No .env files in deployed functions
# - DATABASE_URL, API keys must be configured properly

# CRITICAL: File uploads and audio storage
# - No local file system persistence
# - Audio files must go directly to Supabase Storage
# - Temporary files need careful cleanup
```

### Embeddings on Vercel (Model Size & Strategy)
- The current embeddings service loads HuggingFace 'sentence-transformers/all-MiniLM-L6-v2' in-process ([EmbeddingsService](src/services/embeddings.py:22)). Packaging this model will exceed typical Vercel Python deployment size limits and increase cold start times substantially.
- Recommended production strategies:
  1) Externalize embeddings to a managed API (e.g., Hugging Face Inference API, OpenAI text-embedding-3-small/large, VoyageAI). Replace local model load with HTTP calls; cache results in Supabase or KV.
  2) Split embeddings into a separate service not constrained by Vercel size limits (e.g., a containerized microservice), and call it from the backend.
  3) If keeping in-process temporarily, lazy-load the model on first request and accept higher cold-start latency. Not recommended for production due to size and memory constraints.
- Update plan below assumes option (1) or (2) for production. Keep the local implementation for development.

## Implementation Blueprint

### Data Models and Structure
Core serverless adaptations while preserving business logic:

```python
# NEW: vercel.json
# Fluid Compute configuration for cost optimization
{
  "functions": {
    "api/index.py": {
      "runtime": "python3.11",
      "memory": 1024,
      "maxDuration": 300
    }
  },
  "rewrites": [
    {
      "source": "/api/v1/(.*)",
      "destination": "/api/index"
    }
  ]
}

# FLUID COMPUTE: Existing dependency patterns preserved
# No changes needed to src/api/dependencies.py
# Connection pooling and service caching maintained
# Lifespan handlers work normally
```

### List of Tasks to Complete

```yaml
Phase 1: Fluid Compute Setup (Simplified Architecture)
Task 1.1: Create Fluid Compute Entry Point
  CREATE api/ directory with single entry point
  - IMPORT existing FastAPI app from src.main
  - PRESERVE all business logic from src/ modules
  - MAINTAIN existing architecture patterns

Task 1.2: Tighten Dependencies (no adapters)
  MODIFY requirements.txt:
    - REMOVE Mangum (not needed on Vercel Python)
    - KEEP uvicorn for local development
    - ADD cachetools (required by embeddings service)
    - REVIEW deps to minimize cold start and package size

Task 1.3: Create Main FastAPI Entry (ASGI)
  CREATE api/index.py:
    - IMPORT FastAPI app from src.main
    - EXPOSE ASGI app variable 'app' (no adapters)
    - ENSURE CORS is configured for frontend domain(s)

Phase 2: Vercel Fluid Compute Configuration
Task 2.1: Configure Fluid Compute
  CREATE vercel.json:
    - SET memory and timeout limits for up to 5-minute execution
    - CONFIGURE rewrites for API proxying within backend project
    - DEFINE environment variable mappings

Task 2.2: Preserve Database Connection Patterns
  MAINTAIN existing src/api/dependencies.py:
    - KEEP existing connection pooling patterns
    - PRESERVE existing query patterns and timeouts
    - MAINTAIN current database optimizations

Task 2.3: Scheduler Strategy for Serverless
  - DISABLE in-process scheduler in production (serverless instances are ephemeral)
  - ADD env flag SCHEDULER_ENABLED=false in backend project (default false)
  - IMPLEMENT Vercel Cron (or external worker) to call idempotent endpoints:
    - e.g., POST /api/v1/scheduled/fetch, POST /api/v1/scheduled/digest
  - UPDATE src/services/scheduler to respect SCHEDULER_ENABLED and no-op on serverless

Phase 3: Frontend Configuration
Task 3.1: Configure Next.js API Base URL
  - ADD NEXT_PUBLIC_API_BASE_URL in Vercel (UI project) pointing to backend domain
  - KEEP UI/next.config.ts minimal (no rewrites)
  - PRESERVE existing build optimizations

Task 3.2: Implement Frontend API Client
  - CREATE UI/src/lib/api.ts:
    - USE relative paths in development, absolute NEXT_PUBLIC_API_BASE_URL in production
    - CENTRALIZE fetch helpers and error handling
    - PRESERVE all existing API call patterns

Phase 4: Environment and Security Setup
Task 4.1: Create Vercel Configuration
  CREATE vercel.json:
    - CONFIGURE Python runtime for api/index.py
    - SET memory (1024MB) and maxDuration (300s)
    - ADD rewrites mapping /api/v1/(.*) -> /api/index
    - DEFINE required environment variables in project settings

Task 4.2: Environment Variable Migration
  DOCUMENT environment variables needed in Vercel dashboard (set in the appropriate project: Backend vs UI):
    BACKEND (Python):
    - SUPABASE_URL
    - SUPABASE_ANON_KEY
    - GEMINI_API_KEY
    - ELEVENLABS_API_KEY
    - HF_API_KEY (optional)
    - CORS_ALLOWED_ORIGINS (comma-separated; include UI domain, e.g., https://your-ui.vercel.app)
    - LOG_LEVEL (optional; defaults to INFO)
    - All other configuration values from [Settings](src/config.py)

    FRONTEND (Next.js):
    - NEXT_PUBLIC_API_BASE_URL (e.g., https://your-backend.vercel.app)
    - NEXT_PUBLIC_SUPABASE_URL
    - NEXT_PUBLIC_SUPABASE_ANON_KEY

Phase 5: Testing and Validation
Task 5.1: Local Testing Setup
  CREATE tests/test_api_asgi.py:
    - EXERCISE ASGI app directly with httpx (no adapters)
    - VALIDATE all endpoint responses and error handling
    - CHECK connection pooling preservation within warm instance

Task 5.2: Deployment Testing
  DEPLOY to Vercel staging:
    - VERIFY all 14 endpoints respond correctly
    - TEST database operations and connection pooling
    - VALIDATE audio streaming and TTS pipeline
    - MONITOR performance and cost savings

Phase 6: MCP Server Integration Update
Task 6.1: Update MCP Server URLs (Cloudflare Workers)
  MODIFY mcp-server configuration:
    - ADD/UPDATE environment variables in [wrangler.jsonc](mcp-server/wrangler.jsonc:45):
      - BACKEND_API_BASE_URL = https://your-backend.vercel.app
      - OAUTH callback URLs to point to backend domain (if applicable)
    - UPDATE any hardcoded localhost URLs in [mcp-server/src/](mcp-server/src/index.ts)
    - TEST integration between MCP server and new backend (Workers dev and prod)
    - VALIDATE GitHub OAuth flow with new callback URLs against backend
    - DOCUMENT expected CORS and auth headers between Workers and backend
```

### Per Task Pseudocode

```python
# api/index.py

# Ensure 'src' is importable when project root is the deployment root
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Import the existing FastAPI app directly (ASGI)
from src.main import app  # FastAPI app mounted with prefix '/api/v1'

# Vercel will route '/api/index' here; vercel.json rewrites '/api/v1/*' -> '/api/index'
# No adapters or cloud-provider event handlers required
```

```ts
// UI/src/lib/api.ts
const isProd = typeof window === "undefined"
  ? process.env.NODE_ENV === "production"
  : window.location.hostname.endsWith("vercel.app") || !window.location.hostname.includes("localhost");

export const API_BASE =
  (process.env.NEXT_PUBLIC_API_BASE_URL && isProd)
    ? process.env.NEXT_PUBLIC_API_BASE_URL.replace(/\/+$/, "")
    : (typeof window !== "undefined" ? "" : "http://localhost:8000");

export async function apiGet(path: string, init?: RequestInit) {
  const url = `${API_BASE}${path.startsWith("/") ? path : `/${path}`}`;
  const res = await fetch(url, { ...init, method: "GET" });
  if (!res.ok) throw new Error(`GET ${url} -> ${res.status}`);
  return res.json();
}
```

### Integration Points
```yaml
VERCEL_CONFIGURATION:
  - file: vercel.json
  - pattern: Configure Python runtime, memory, maxDuration, and path-to-path rewrites
  - critical: Use supported runtime (e.g., python3.11) and rewrites '/api/v1/*' -> '/api/index'
  - benefit: Simplified routing and predictable latency

DATABASE:
  - preservation: Keep existing connection pooling patterns
  - advantage: Connection pools work normally in Fluid Compute
  - timeout: Existing query patterns maintained (5-minute limit)
  - pooling: Supabase client connection pooling preserved

ENVIRONMENT:
  - production: All secrets in Vercel dashboard environment variables
  - development: Local .env files preserved for dev workflow
  - security: No hardcoded credentials in deployed code

MCP_SERVER:
  - update: Webhook URLs changed from localhost to Vercel deployment
  - test: GitHub OAuth integration with new callback URLs
  - monitor: Rate limiting and error tracking for production traffic

FRONTEND:
  - api-base-url: Use environment variable NEXT_PUBLIC_API_BASE_URL pointing to backend domain
  - fetches: Client/Server fetch via absolute URL in production, relative in dev
  - deploy: Separate Vercel project for UI (root = UI/)
```

## Validation Loop

### Level 1: Local Development & Syntax
```bash
# Syntax and type checking
ruff check . --fix
mypy src/ api/

# Local ASGI smoke test with httpx
python - <<'PY'
import asyncio
from httpx import AsyncClient
from src.main import app

async def main():
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        r = await ac.get("/api/v1/health")
        print(r.status_code, r.text)

asyncio.run(main())
PY
# Expected: 200 and JSON body
```

### Level 2: Unit Tests for Fluid Compute Functions
```python
# CREATE tests/test_api_asgi.py
import pytest
from httpx import AsyncClient
from src.main import app

@pytest.mark.asyncio
async def test_health_endpoint():
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        resp = await ac.get("/api/v1/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("status") in {"healthy", "ok", "running"}

@pytest.mark.asyncio
async def test_articles_endpoint():
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        resp = await ac.get("/api/v1/articles", params={"page": 1, "per_page": 5})
    assert resp.status_code == 200
    data = resp.json()
    assert "articles" in data
    assert isinstance(data["articles"], list)
    assert len(data["articles"]) <= 5
```

```bash
# Run tests locally
pytest tests/test_api_asgi.py -v

# Expected: ASGI endpoints respond correctly and pooling works per warm instance
```

### Level 3: Vercel Deployment Test
```bash
# Deploy backend (Python project root) to Vercel
vercel --prod

# Test deployed backend endpoints (replace with your backend project domain)
curl -sS "https://your-backend.vercel.app/api/v1/health"

curl -sS "https://your-backend.vercel.app/api/v1/articles?page=1&per_page=5"

curl -sS "https://your-backend.vercel.app/api/v1/stats"

# Test audio streaming headers
curl -I "https://your-backend.vercel.app/api/v1/digests/latest/audio"
```

### Level 4: Performance & Cost Monitoring
```bash
# Monitor function execution in Vercel dashboard
# Check: Cold vs warm starts, memory usage, execution duration
# Target: p50 < 1s, p95 < 2s, memory < 512MB
# Note: Validate cost savings empirically in Usage tab

# Validate within Fluid Compute limits
# Monitor: CPU-hours usage and instance reuse
# Check: Function invocation count and error rates

# Test database connection efficiency
# Monitor: Active connections in Supabase dashboard
# Target: Connection pooling working, optimized concurrent connections
```

## Final Validation Checklist
- [ ] All 14 API endpoints deployed and responding correctly
- [ ] Frontend successfully calling backend domain with CORS passing
- [ ] Database connections working without leaks or timeouts
- [ ] Environment variables configured securely in Vercel
- [ ] Audio streaming and TTS pipeline operational in production
- [ ] MCP server (Cloudflare Workers) updated to call backend domain; OAuth/webhooks verified
- [ ] Performance monitoring shows <2s response times
- [ ] Cost monitoring shows usage within free tier limits
- [ ] Error tracking configured and functional
- [ ] Health checks passing consistently
- [ ] All tests pass: `pytest tests/ -v`
- [ ] No security vulnerabilities in dependencies
- [ ] Documentation updated with production URLs

## MCP Tool Integration Strategy

### Context7 MCP Usage
```bash
# Get latest FastAPI Fluid Compute deployment patterns
mcp__context7__get-library-docs /tiangolo/fastapi "vercel deployment mangum production"

# Get Vercel Fluid Compute Python runtime documentation  
mcp__context7__get-library-docs /vercel/vercel "python functions fluid compute concurrency"

# Research connection pooling best practices
mcp__context7__get-library-docs /supabase/supabase "connection pooling python performance"
```

### Supabase MCP Usage
```bash
# Test database connections during deployment
mcp__supabase__execute_sql "SELECT COUNT(*) FROM articles"

# Monitor performance after deployment
mcp__supabase__get_advisors "performance"

# Check for connection leaks
mcp__supabase__get_logs "postgres"
```

### Playwright MCP Usage (Optional)
```bash
# Test deployed frontend end-to-end
mcp__playwright__browser_navigate "https://your-project.vercel.app"
mcp__playwright__browser_snapshot  # Verify UI loads correctly
mcp__playwright__browser_click "search button"  # Test interactions
```

## Critical Considerations

### Database Connection Strategy
- **Connection Pooling Preserved**: Existing patterns work in Fluid Compute
- **Extended Timeouts**: Up to 5-minute execution time available
- **No Explicit Cleanup Needed**: Connection pools managed normally
- **Connection Monitoring**: Optimize concurrent connections in Supabase dashboard

### Fluid Compute Characteristics
- Reduced cold start impact compared to traditional serverless
- Extended maxDuration (up to ~300s) for long-running requests
- Connection pooling can be reused within a warm instance
- Cost efficiency from instance reuse and generous free tier

### Error Handling & Logging
- **Structured Logging**: JSON logs for Vercel dashboard analysis
- **Error Boundaries**: Graceful handling of database timeouts
- **Monitoring Integration**: Set up alerts for function failures
- **Retry Logic**: Implement exponential backoff for transient failures

### Security Best Practices
- **Environment Variables**: All secrets in Vercel dashboard
- **CORS Configuration**: Restrict origins to production domains
- **API Documentation**: Disable in production (/docs, /redoc)
- **Rate Limiting**: Implement per-IP rate limiting for public endpoints

## Fallback Strategies

### If Deployment Size Exceeds 50MB
1. **Dependency Optimization**: Remove unnecessary packages
2. **Function Splitting**: Split into smaller, specialized functions
3. **External Dependencies**: Move large models to external services
4. **Container Deployment**: Switch to Vercel's container runtime

### If Function Timeout Issues
1. **Query Optimization**: Add database indexes for slow queries  
2. **Async Optimization**: Ensure all I/O is properly async
3. **Extended Duration**: Use up to 5-minute execution time in Fluid Compute
4. **Background Processing**: Long tasks supported with extended timeouts

### If Cost Exceeds Free Tier
1. **Function Optimization**: Reduce CPU-intensive operations
2. **Caching Strategy**: Implement response caching to reduce invocations
3. **Batch Processing**: Combine multiple operations per invocation
4. **Upgrade Plan**: Move to Pro plan ($20/month) for higher limits

## Confidence Score: 9/10

**Confidence Assessment:**
- **High (9/10)**: This PRP provides comprehensive implementation details with:
  - Simplified Fluid Compute deployment approach
  - Detailed validation loops with executable tests
  - Preservation of existing architecture and patterns
  - Integration with existing, working codebase (100% complete)
  - 85% cost savings with Fluid Compute benefits
  - MCP tool integration for validation and monitoring

**Deducted 1 point for:**
- First-time serverless deployment complexity
- Potential edge cases in database connection cleanup
- Need for iterative performance optimization in production

The existing codebase is production-ready and this PRP provides a clear path to successful Vercel deployment with minimal risk and maximum reuse of working components.

---

## Anti-Patterns to Avoid
- ❌ Don't implement new business logic during deployment - only adapt existing code
- ❌ Don't skip database connection cleanup - causes connection leaks
- ❌ Don't run long-lived schedulers inside serverless functions — use Vercel Cron or an external worker
- ❌ Don't hardcode URLs or secrets in deployed code - use environment variables
- ❌ Don't ignore function timeout limits - optimize queries and add timeouts
- ❌ Don't deploy without testing locally first — validate ASGI endpoints with httpx/pytest
- ❌ Don't forget to update MCP server URLs - breaks integration
- ❌ Don't skip performance monitoring - Vercel provides detailed metrics