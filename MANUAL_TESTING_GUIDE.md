# 🧪 Manual Testing Guide

## Prerequisites

1. **Environment Setup**
   ```bash
   source venv_linux/bin/activate
   pip install -r requirements.txt
   ```

2. **Environment Variables** (check your `.env` file)
   ```env
   SUPABASE_URL=your_supabase_url
   SUPABASE_ANON_KEY=your_anon_key
   GEMINI_API_KEY=your_gemini_key
   ELEVENLABS_API_KEY=your_elevenlabs_key  # Optional
   ```

## 🚀 Start the Application

```bash
# Start FastAPI server with auto-reload
python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

The application will be available at:
- **API**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🔍 Testing Modules

### 1. Health Check & System Status

```bash
# Basic health check
curl http://localhost:8000/health

# System performance metrics
curl http://localhost:8000/monitoring/performance

# Rate limiter status
curl http://localhost:8000/monitoring/rate-limits

# Scheduler status
curl http://localhost:8000/scheduler/status
```

**Expected Results:**
- Health endpoint returns `{"status": "healthy"}`
- Performance shows CPU, memory usage
- Rate limits show current token counts
- Scheduler shows running tasks

### 2. Data Fetchers Testing

#### Test Individual Fetchers
```bash
# ArXiv papers (should respect 3-second rate limit)
curl http://localhost:8000/test/fetchers/arxiv

# HackerNews stories
curl http://localhost:8000/test/fetchers/hackernews

# RSS feeds (includes YouTube channels)
curl http://localhost:8000/test/fetchers/rss

# Reddit discussions
curl http://localhost:8000/test/fetchers/reddit

# GitHub releases
curl http://localhost:8000/test/fetchers/github

# HuggingFace models
curl http://localhost:8000/test/fetchers/huggingface
```

**What to Verify:**
- Each fetcher returns 5-50 articles
- Articles have proper source attribution
- No rate limit errors (429 status)
- Response time under 30 seconds

#### Test Configuration Hot-Reload
1. **Modify config files:**
   ```bash
   # Add a new GitHub repo
   echo '"microsoft/semantic-kernel"' >> config/github_repos.json
   
   # Add a new subreddit
   echo '"artificial"' >> config/reddit_subs.json
   ```

2. **Trigger fetch and verify:**
   ```bash
   curl -X POST http://localhost:8000/scheduler/task/fetch_all_sources/run
   curl http://localhost:8000/articles?source=github&limit=10
   ```

### 3. Database Operations

#### View Stored Articles
```bash
# Get recent articles
curl http://localhost:8000/articles?limit=10

# Filter by source
curl "http://localhost:8000/articles?source=arxiv&limit=5"

# Check article count
curl http://localhost:8000/articles/count
```

#### Test Article Storage
```bash
# Trigger a manual fetch (stores to DB)
curl -X POST http://localhost:8000/scheduler/task/fetch_all_sources/run

# Wait 30 seconds, then check if articles increased
curl http://localhost:8000/articles/count
```

### 4. AI Analysis & Digest Generation

#### Test Article Analysis
```bash
# Get an article ID first
ARTICLE_ID=$(curl -s http://localhost:8000/articles?limit=1 | jq -r '.[0].id')

# Analyze article (if not already analyzed)
curl -X POST http://localhost:8000/analyze/article/$ARTICLE_ID
```

#### Test Digest Generation
```bash
# Generate daily digest
curl -X POST "http://localhost:8000/digests/generate?limit=10"

# Get latest digest
curl http://localhost:8000/digests/latest

# List all digests
curl http://localhost:8000/digests/
```

### 5. Deduplication Testing

#### Create Test Duplicates
```bash
# This requires direct database access - use Supabase dashboard
# Or create a test script to insert near-identical articles
```

#### Verify Deduplication
```bash
# Check for duplicate articles in same timeframe
curl "http://localhost:8000/articles?limit=50" | jq '[.[] | {title, source, is_duplicate}]'
```

### 6. Scheduled Tasks

#### Manual Task Execution
```bash
# Run all fetchers
curl -X POST http://localhost:8000/scheduler/task/fetch_all_sources/run

# Generate daily digest
curl -X POST http://localhost:8000/scheduler/task/generate_daily_digest/run

# Check task history
curl http://localhost:8000/scheduler/tasks
```

#### Monitor Task Execution
```bash
# Check logs (if logging to file)
tail -f logs/app.log

# Or monitor via API
watch -n 5 "curl -s http://localhost:8000/scheduler/status"
```

### 7. Audio Generation (TTS)

```bash
# Generate audio for latest digest
DIGEST_ID=$(curl -s http://localhost:8000/digests/latest | jq -r '.id')
curl -X POST http://localhost:8000/digests/$DIGEST_ID/generate-audio

# Check if audio file was created
curl http://localhost:8000/digests/$DIGEST_ID/audio
```

## 🔧 Troubleshooting

### Common Issues

1. **Rate Limit Errors (429)**
   ```bash
   # Check rate limit status
   curl http://localhost:8000/monitoring/rate-limits
   # Wait for tokens to replenish
   ```

2. **Database Connection Issues**
   ```bash
   # Verify Supabase credentials
   curl http://localhost:8000/health
   # Check .env file configuration
   ```

3. **Fetcher Failures**
   ```bash
   # Check specific fetcher logs
   curl http://localhost:8000/test/fetchers/arxiv
   # Verify API keys in .env
   ```

### Debug Mode

Start with debug logging:
```bash
LOG_LEVEL=DEBUG python -m uvicorn src.main:app --reload
```

### Performance Testing

```bash
# Load test with multiple concurrent requests
for i in {1..10}; do
  curl http://localhost:8000/articles?limit=10 &
done
wait

# Check response times
time curl http://localhost:8000/articles?limit=100
```

## 📋 Verification Checklist

### ✅ Backend Health
- [ ] Health endpoint responds
- [ ] Database connection works
- [ ] All 7 fetchers return data
- [ ] No rate limit violations
- [ ] Articles stored correctly
- [ ] Deduplication working
- [ ] AI analysis generates summaries
- [ ] Daily digest creation works
- [ ] Scheduled tasks execute
- [ ] Configuration hot-reload works

### ✅ Performance
- [ ] Article fetch under 30s
- [ ] API responses under 3s
- [ ] No memory leaks during extended run
- [ ] Rate limits respected
- [ ] Concurrent requests handled

### ✅ Data Quality
- [ ] Articles have proper metadata
- [ ] Summaries are coherent
- [ ] Relevance scores reasonable (0-100)
- [ ] Source attribution correct
- [ ] Timestamps accurate
- [ ] No duplicate content

## 🚨 Known Issues

1. **Reddit Fetcher**: Requires Reddit API credentials
2. **HuggingFace**: Rate limited without API key
3. **Audio Generation**: Requires ElevenLabs API key
4. **GitHub**: Rate limited without token (60 req/hour vs 5000)

## 📊 Success Metrics

- **Uptime**: >99% for scheduled tasks
- **Data Quality**: <5% duplicates
- **Performance**: <3s API response time
- **Coverage**: All 7 sources fetching successfully
- **Tests**: 181/181 passing