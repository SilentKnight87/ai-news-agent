# 🚀 Vercel Deployment Specification

## Overview

This specification outlines the complete deployment strategy for the AI News Aggregator to Vercel, utilizing Vercel's Fluid Compute for the backend API and standard hosting for the Next.js frontend.

**Architecture:**
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │    │   MCP Server     │    │  Backend API    │
│   (Vercel       │◄──►│  (Cloudflare     │◄──►│   (Vercel       │
│   Static)       │    │   Workers)       │    │   Functions)    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                        │                        │
         └────────────────────────┼────────────────────────┘
                                  ▼
                          ┌─────────────────┐
                          │   Supabase DB   │
                          │   (PostgreSQL   │
                          │   + pgvector)   │
                          └─────────────────┘
```

## Benefits of Vercel Deployment

### 🎯 Why Vercel Fluid Compute for Backend?
- **Perfect for AI workloads**: 85-90% cost savings on LLM/AI operations
- **Generous free tier**: 4 CPU-hours + 360 GB-hours memory + 1M invocations
- **No cold starts**: Fluid compute eliminates serverless cold start issues
- **Only pay for active CPU**: Waiting for Gemini API responses doesn't count
- **Seamless integration**: Same platform as frontend

### 🏗️ Architecture Advantages
- **Single platform**: One dashboard, one billing, one deployment pipeline
- **No CORS issues**: Backend and frontend on same domain
- **Shared environment**: Common env vars and configuration
- **Auto-scaling**: Built-in scaling for traffic spikes
- **Global CDN**: Automatic edge distribution

## Deployment Plan

### Phase 1: Backend API to Vercel Functions

#### 1.1 Project Structure Changes

Create the following directory structure:
```
ai-news-aggregator-agent/
├── api/                    # Vercel Functions (NEW)
│   ├── index.py           # Main FastAPI app adapter
│   ├── health.py          # Health check endpoint
│   ├── articles.py        # Articles endpoints
│   ├── digests.py         # Digests endpoints
│   ├── stats.py           # Stats endpoint
│   └── webhook/           # Webhook endpoints
│       ├── fetch.py       # Fetch webhook
│       └── scheduler.py   # Scheduler webhook
├── src/                   # Existing backend code (KEEP)
├── vercel.json            # Vercel configuration (NEW)
├── requirements.txt       # Python dependencies (UPDATE)
└── ...
```

#### 1.2 Create `vercel.json` Configuration

```json
{
  "version": 2,
  "builds": [
    {
      "src": "api/**/*.py",
      "use": "@vercel/python",
      "config": {
        "runtime": "python3.11"
      }
    },
    {
      "src": "UI/package.json",
      "use": "@vercel/next"
    }
  ],
  "routes": [
    {
      "src": "/api/v1/(.*)",
      "dest": "/api/index.py"
    },
    {
      "src": "/((?!api/).*)",
      "dest": "/UI/$1"
    }
  ],
  "env": {
    "PYTHON_PATH": "/var/task",
    "SUPABASE_URL": "@supabase_url",
    "SUPABASE_ANON_KEY": "@supabase_anon_key",
    "GEMINI_API_KEY": "@gemini_api_key",
    "ELEVENLABS_API_KEY": "@elevenlabs_api_key",
    "SIMILARITY_THRESHOLD": "0.85",
    "FETCH_INTERVAL_MINUTES": "30",
    "DIGEST_HOUR_UTC": "17",
    "DEBUG": "false",
    "LOG_LEVEL": "INFO"
  },
  "functions": {
    "api/**/*.py": {
      "runtime": "python3.11",
      "memory": 1024,
      "maxDuration": 60
    }
  }
}
```

#### 1.3 Create API Function Adapters

**`api/index.py` - Main FastAPI Adapter:**
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sys
import os

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.main import app as fastapi_app

# Configure for Vercel
app = fastapi_app

# Update CORS for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for your domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Vercel handler
def handler(request, context):
    return app(request, context)
```

**Individual endpoint functions for better performance:**

**`api/health.py`:**
```python
from fastapi import FastAPI
from src.api.routes.health import router as health_router

app = FastAPI()
app.include_router(health_router, prefix="/api/v1")
```

**`api/articles.py`:**
```python
from fastapi import FastAPI
from src.api.routes.articles import router as articles_router

app = FastAPI()
app.include_router(articles_router, prefix="/api/v1")
```

#### 1.4 Update Requirements for Vercel

**`requirements.txt` additions:**
```
# Vercel-specific
mangum>=0.17.0
python-multipart>=0.0.6

# Existing dependencies
fastapi>=0.104.1
uvicorn>=0.24.0
sqlalchemy>=2.0.23
asyncpg>=0.29.0
# ... rest of existing requirements
```

### Phase 2: Frontend Deployment to Vercel

#### 2.1 Update Frontend Configuration

**Update `UI/next.config.js`:**
```javascript
/** @type {import('next').NextConfig} */
const nextConfig = {
  env: {
    CUSTOM_KEY: 'my-value',
  },
  async rewrites() {
    return [
      {
        source: '/api/v1/:path*',
        destination: '/api/:path*', // Proxy to Vercel Functions
      },
    ]
  },
  experimental: {
    serverComponentsExternalPackages: [],
  },
}

module.exports = nextConfig
```

#### 2.2 Update API Calls in Frontend

**Update all API calls to use relative paths:**
```typescript
// Before: http://localhost:8000/api/v1/articles
// After: /api/v1/articles

const API_BASE_URL = process.env.NODE_ENV === 'production' 
  ? '/api/v1' 
  : 'http://localhost:8000/api/v1';
```

### Phase 3: Environment Variables Configuration

#### 3.1 Vercel Environment Variables

Set up the following environment variables in Vercel dashboard:

**Production Environment:**
```
SUPABASE_URL=your_supabase_project_url
SUPABASE_ANON_KEY=your_supabase_anon_key
GEMINI_API_KEY=your_google_gemini_api_key
ELEVENLABS_API_KEY=your_elevenlabs_api_key
SIMILARITY_THRESHOLD=0.85
FETCH_INTERVAL_MINUTES=30
DIGEST_HOUR_UTC=17
DEBUG=false
LOG_LEVEL=INFO
```

**Frontend Environment Variables:**
```
NEXT_PUBLIC_API_BASE_URL=/api/v1
NEXT_PUBLIC_MCP_SERVER_URL=https://my-mcp-server.pbrow35.workers.dev/mcp
```

### Phase 4: Deployment Commands

#### 4.1 Install Vercel CLI
```bash
npm i -g vercel
vercel login
```

#### 4.2 Deploy Backend + Frontend
```bash
# From project root
vercel --prod

# Or step by step:
vercel deploy --prod --name ai-news-aggregator
```

#### 4.3 Test Deployment
```bash
# Test API endpoints
curl https://your-project.vercel.app/api/v1/health
curl https://your-project.vercel.app/api/v1/stats
curl https://your-project.vercel.app/api/v1/articles?limit=5

# Test frontend
open https://your-project.vercel.app
```

## Performance Optimization

### 🚀 Vercel Fluid Compute Benefits for AI Workloads

1. **Active CPU Billing**: Only pay when code is executing
2. **I/O Wait Optimization**: Gemini API calls don't consume CPU time
3. **Memory Pooling**: Efficient memory usage across requests
4. **Connection Reuse**: Persistent database connections

### 📊 Expected Performance

**Free Tier Capacity:**
- **4 CPU-hours/month** = ~14,400 seconds of active processing
- **360 GB-hours memory** = Sufficient for 1GB functions running 15 days/month
- **1M invocations** = 33,000 requests/day average

**Realistic Usage for News Aggregator:**
- Typical request: 50-100ms active CPU (database + processing)
- AI analysis: 20-50ms active CPU (waiting for Gemini doesn't count)
- **Estimated capacity**: 50,000+ requests/month on free tier

## Monitoring and Maintenance

### 📊 Vercel Analytics
- Built-in Web Analytics for frontend
- Function logs and performance monitoring
- Real-time error tracking

### 🔍 Custom Monitoring
```python
# Add to main application
import logging
from vercel import logger

@app.middleware("http")
async def monitor_performance(request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    
    logger.info(f"Request {request.url.path} took {process_time:.3f}s")
    return response
```

### 🚨 Health Checks
```python
# api/health.py
from fastapi import FastAPI, HTTPException
from datetime import datetime

@app.get("/api/v1/health")
async def health_check():
    try:
        # Test database connection
        # Test external API access
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow(),
            "environment": "production",
            "platform": "vercel"
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))
```

## Security Considerations

### 🔐 Production Security
- Environment variables stored securely in Vercel
- HTTPS by default
- CORS properly configured
- Input validation with Pydantic
- Rate limiting via Vercel Edge Config

### 🛡️ API Security Enhancements
```python
# Add to production deployment
from fastapi.middleware.trustedhost import TrustedHostMiddleware

app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=["your-project.vercel.app", "*.vercel.app"]
)
```

## Post-Deployment Tasks

### ✅ Immediate Tasks After Deployment
1. **Update MCP Server**: Point webhook URLs to Vercel deployment
2. **Test Integration**: Verify frontend ↔ backend ↔ MCP server communication
3. **Monitor Logs**: Check Vercel function logs for any issues
4. **Performance Testing**: Load test with expected traffic patterns
5. **Documentation Update**: Update README with production URLs

### 🔄 Ongoing Maintenance
1. **Monitor Usage**: Track Vercel function usage against free tier limits
2. **Performance Optimization**: Use Vercel Analytics to identify bottlenecks
3. **Scaling Planning**: Monitor for when to upgrade to Pro plan
4. **Security Updates**: Regular dependency updates and security patches

## Cost Management

### 💰 Free Tier Monitoring
- **4 CPU-hours**: Monitor via Vercel dashboard
- **360 GB-hours memory**: Track memory usage patterns
- **1M invocations**: Set up alerts at 80% usage

### 📈 Scaling Plan
- **Pro Plan ($20/month)**: 16 CPU-hours + 1440 GB-hours memory
- **Usage-based pricing**: Additional CPU/memory as needed
- **Enterprise**: Custom pricing for high-scale deployments

### 🎯 Optimization Tips
1. **Cache responses** where possible
2. **Optimize database queries** to reduce CPU time
3. **Use appropriate memory allocation** (1GB for AI workloads)
4. **Implement request batching** for bulk operations

## Success Metrics

### 📊 Key Performance Indicators
- **Response Time**: < 2s for API endpoints
- **Uptime**: 99.9% availability
- **Error Rate**: < 0.1%
- **Cost Efficiency**: Stay within free tier for MVP

### 🎯 Launch Readiness Checklist
- [ ] Backend API deployed and responsive
- [ ] Frontend deployed and accessing API correctly
- [ ] MCP server updated with new webhook URLs
- [ ] Environment variables configured
- [ ] Health checks passing
- [ ] Performance monitoring active
- [ ] Error tracking configured
- [ ] Domain configured (if custom domain)
- [ ] SSL certificates active
- [ ] Documentation updated with production URLs

---

## 🚀 Ready for Production

This specification provides a complete roadmap for deploying the AI News Aggregator to Vercel using Fluid Compute for optimal performance and cost efficiency. The deployment leverages Vercel's strengths for both frontend and backend hosting while maintaining the existing architecture and functionality.

**Next Steps**: Execute Phase 1 (Backend API restructure) → Phase 2 (Frontend updates) → Phase 3 (Environment setup) → Phase 4 (Deploy)