# GitHub Actions Direct Execution Implementation PRP

## Goal
Implement direct execution of Python pipeline tasks via GitHub Actions runners to restore the AI News Aggregator pipeline that has been dormant since August 10th. This will enable automated article fetching (every 30 minutes) and daily digest generation (at 5 PM UTC) without requiring backend infrastructure deployment.

## Why
- **Pipeline Restoration**: Articles haven't been fetched since August 10th; no digests generated
- **Cost Efficiency**: Utilize GitHub Actions free tier (2,000 minutes/month) instead of paid hosting
- **Portfolio Value**: Demonstrates CI/CD expertise with transparent execution logs
- **Immediate Value**: 2-4 hour implementation vs days of infrastructure refactoring
- **Zero Architecture Changes**: Reuses existing FastAPI/scheduler code without modifications

## What
Implement CLI wrappers around existing scheduler functions and GitHub Actions workflows to execute pipeline tasks directly on GitHub's infrastructure.

### Success Criteria
- [ ] Articles are fetched every 30 minutes and stored in Supabase
- [ ] Daily digest is generated at 5 PM UTC with optional audio
- [ ] Execution logs are visible in GitHub Actions for portfolio demonstration
- [ ] Service role key enables write operations to Supabase
- [ ] Gemini embeddings eliminate model download overhead
- [ ] Monthly GitHub Actions usage stays under 1,000 minutes (50% of free tier)

## All Needed Context

### Documentation & References
```yaml
- file: spec/github-actions-direct-execution.md
  why: Complete specification with GPT-5's critical adjustments and implementation details
  
- file: src/services/scheduler.py
  lines: 391-477
  why: Contains fetch_all_sources() and generate_daily_digest() functions to wrap
  
- file: src/api/dependencies.py
  lines: 26-63
  why: get_supabase_client() needs modification for service role key
  
- file: src/config.py
  lines: 20-57
  why: Settings class with environment variables configuration

- url: https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions
  why: GitHub Actions workflow syntax reference
  
- url: https://supabase.com/docs/guides/api/api-keys
  why: Service role key documentation for write operations

- mcp: mcp__supabase__list_tables
  why: Current database schema - articles, daily_digests, digest_articles tables exist
```

### Current Codebase Structure
```bash
ai-news-aggregator-agent/
├── src/
│   ├── services/
│   │   └── scheduler.py         # Contains functions to wrap
│   ├── api/
│   │   └── dependencies.py      # Needs service role key modification
│   └── config.py                 # Settings configuration
├── requirements.txt              # Minimal (supabase, httpx) - needs expansion
└── spec/
    └── github-actions-direct-execution.md  # Full specification
```

### Desired Codebase Structure
```bash
ai-news-aggregator-agent/
├── scripts/                      # NEW: CLI wrapper scripts
│   ├── fetch_articles.py        # Wraps fetch_all_sources()
│   └── generate_digest.py       # Wraps generate_daily_digest()
├── .github/
│   └── workflows/               # NEW: GitHub Actions workflows
│       └── pipeline.yml         # Scheduled and manual triggers
├── src/
│   ├── api/
│   │   └── dependencies.py     # MODIFIED: Service role key support
│   └── [unchanged]
└── requirements.txt             # MODIFIED: Full dependencies restored
```

### Known Gotchas & Critical Requirements
```python
# CRITICAL: Supabase service role key required for write operations
# GitHub Actions uses SUPABASE_SERVICE_ROLE_KEY env var, not anon key

# CRITICAL: Set EMBEDDINGS_PROVIDER=gemini to avoid 500MB model downloads
# Uses existing GEMINI_API_KEY for both AI analysis and embeddings

# GOTCHA: requirements.txt currently minimal for Vercel
# Must restore FastAPI, pydantic, fetcher dependencies (but NOT uvicorn/sqlalchemy)

# CRITICAL: fetch_all_sources and generate_daily_digest are INNER functions
# Cannot import directly - must use setup_default_tasks() + run_task_now()

# PATTERN: Use existing scheduler functions via run_task_now()
# Don't reimplement logic, just wrap existing tested code

# GOTCHA: Both jobs run on workflow_dispatch without proper conditions
# Must gate jobs with schedule AND dispatch.task conditions

# GOTCHA: GitHub Actions uses UTC for cron schedules
# Daily digest at "0 17 * * *" = 5 PM UTC
```

## Implementation Blueprint

### Data Models and Structure
No new models needed - reusing existing:
- `src/services/scheduler.py`: ScheduledTask, TaskScheduler classes
- `src/config.py`: Settings class with pydantic validation
- Database tables already exist: articles, daily_digests, digest_articles

### Task List

```yaml
Task 1: Update dependencies
MODIFY requirements.txt:
  - REPLACE minimal Vercel dependencies
  - ADD only required packages for CLI execution path:
    # Core (required for imports)
    fastapi
    pydantic>=2.5.0
    pydantic-settings
    python-dotenv
    # Data fetching
    arxiv
    feedparser
    httpx
    aiohttp
    # Database
    supabase
    # Utilities
    tenacity
    # Optional (uncomment if needed)
    # elevenlabs  # Only if TTS enabled
    # NOTE: Do NOT add uvicorn or sqlalchemy unless needed

Task 2: Modify Supabase client for service role key
MODIFY src/api/dependencies.py:
  - FIND function: get_supabase_client()
  - ADD import: import os
  - MODIFY client creation to prefer service role key:
    service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    key_to_use = service_key if service_key else settings.supabase_anon_key
  - UPDATE create_client() call to use key_to_use

Task 3: Create fetch articles CLI wrapper
CREATE scripts/fetch_articles.py:
  - IMPORT setup_default_tasks, get_scheduler from src/services/scheduler
  - NOTE: Do NOT try to import fetch_all_sources directly (it's an inner function)
  - ADD execution timing and GitHub step summary output
  - IMPLEMENT error handling with proper exit codes
  - PATTERN: Call setup_default_tasks() then run_task_now("fetch_articles")

Task 4: Create digest generation CLI wrapper  
CREATE scripts/generate_digest.py:
  - MIRROR pattern from fetch_articles.py
  - CALL run_task_now("daily_digest") instead
  - ADD GitHub step summary for portfolio visibility

Task 5: Create GitHub Actions workflow
CREATE .github/workflows/pipeline.yml:
  - ADD cron schedules for fetch (*/30) and digest (0 17)
  - ADD workflow_dispatch with task selection input (fetch, digest, both)
  - CONFIGURE job conditions to properly gate on schedule AND dispatch input
  - CONFIGURE concurrency groups to prevent overlaps
  - SET environment variables including EMBEDDINGS_PROVIDER=gemini
  - ENABLE pip caching via actions/setup-python
```

### Per-Task Implementation Details

```python
# Task 2: Service role key modification
@lru_cache
def get_supabase_client() -> Client:
    import os  # Add this import
    settings = get_settings()
    
    # Prefer service role key for write operations (GitHub Actions)
    service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    key_to_use = service_key if service_key else settings.supabase_anon_key
    
    # ... existing ClientOptions code ...
    
    client = create_client(
        settings.supabase_url,
        key_to_use,  # Use service key if available
        options=options
    )
    return client

# Task 3: Fetch articles wrapper pattern (CORRECT)
# NOTE: fetch_all_sources is an inner function, not directly importable
from src.services.scheduler import setup_default_tasks, get_scheduler

async def main():
    """CLI wrapper for article fetching."""
    start_time = time.time()
    print(f"🚀 Starting article fetch at {datetime.utcnow().isoformat()}Z")
    
    try:
        # Setup creates the inner functions and registers tasks
        await setup_default_tasks()
        scheduler = get_scheduler()
        
        # Execute using task name (calls the inner fetch_all_sources)
        success = await scheduler.run_task_now("fetch_articles")
        execution_time = time.time() - start_time
        
        # GitHub Actions summary output
        if success and os.getenv("GITHUB_STEP_SUMMARY"):
            with open(os.getenv("GITHUB_STEP_SUMMARY"), "a") as f:
                f.write(f"## 📰 Article Fetch Summary\n")
                f.write(f"- **Duration**: {execution_time:.2f}s\n")
            
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Fetch failed: {e}")
        sys.exit(1)
```

### Integration Points
```yaml
GITHUB_SECRETS:
  - SUPABASE_URL: Project URL from Supabase dashboard
  - SUPABASE_SERVICE_ROLE_KEY: Service role key (NOT anon key!)
  - GEMINI_API_KEY: For AI analysis and embeddings
  - ELEVENLABS_API_KEY: Optional for TTS (only if queueing audio)
  
ENVIRONMENT_VARIABLES:
  - EMBEDDINGS_PROVIDER: Set to "gemini" in workflow (avoid model downloads)
  - GITHUB_STEP_SUMMARY: Auto-set by GitHub for summary output
  - LOG_LEVEL: Optional, set to "INFO" for debugging
  
WORKFLOW_CONFIG:
  - schedule: Cron expressions for periodic execution
  - workflow_dispatch: Manual trigger with task selection input
  - concurrency: Prevent overlapping runs with job-specific groups
  - cache: Enable pip caching via actions/setup-python
  
JOB_CONDITIONS:
  - fetch: (schedule == '*/30 * * * *') OR (dispatch && task == 'fetch')
  - digest: (schedule == '0 17 * * *') OR (dispatch && task == 'digest')
```

## Validation Loop

### Level 1: Syntax & Style
```bash
# After creating scripts
ruff check scripts/ --fix
mypy scripts/

# After modifying dependencies.py
ruff check src/api/dependencies.py --fix
mypy src/api/dependencies.py
```

### Level 2: Local Testing
```bash
# Test with local environment variables
export SUPABASE_URL="your-project-url"
export SUPABASE_SERVICE_ROLE_KEY="your-service-key"
export GEMINI_API_KEY="your-gemini-key"
export EMBEDDINGS_PROVIDER="gemini"

# Test CLI wrappers
python scripts/fetch_articles.py
# Expected: Articles fetched and stored in Supabase

python scripts/generate_digest.py  
# Expected: Digest generated (check daily_digests table)
```

### Level 3: GitHub Actions Testing
```bash
# Push changes to repository
git add .
git commit -m "feat: implement GitHub Actions direct execution"
git push

# Manually trigger workflow
# Go to Actions tab → AI News Pipeline → Run workflow
# Select task: fetch, digest, or both

# Verify execution
# Check Actions tab for green checkmarks
# Check Supabase tables for new data
```

### MCP Validation
```bash
# Use Supabase MCP to verify data persistence
mcp__supabase__execute_sql(
  query="SELECT COUNT(*) FROM articles WHERE fetched_at > NOW() - INTERVAL '1 hour'"
)

# Check for recent digests
mcp__supabase__execute_sql(
  query="SELECT * FROM daily_digests ORDER BY created_at DESC LIMIT 1"
)
```

## Final Validation Checklist
- [ ] Dependencies installed: `pip install -r requirements.txt`
- [ ] No linting errors: `ruff check scripts/ src/api/`
- [ ] No type errors: `mypy scripts/ src/api/`
- [ ] Local test successful: Both CLI scripts execute without errors
- [ ] Service role key works: Data written to Supabase
- [ ] GitHub workflow runs: Manual trigger successful
- [ ] Scheduled execution works: Cron triggers activate
- [ ] Step summaries appear: Portfolio-friendly output visible
- [ ] Gemini embeddings work: No model downloads, fast execution
- [ ] Under 2 minutes per task: Performance optimized

## Anti-Patterns to Avoid
- ❌ Don't use anon key for GitHub Actions - needs service role key
- ❌ Don't skip EMBEDDINGS_PROVIDER=gemini - causes 500MB downloads
- ❌ Don't reimplement scheduler logic - reuse existing functions
- ❌ Don't hardcode secrets - use GitHub Secrets
- ❌ Don't ignore exit codes - CLI must return proper status
- ❌ Don't skip concurrency control - prevents overlapping runs

## MCP Tool Usage

### Pre-Implementation Validation
```python
# Verify current database state
mcp__supabase__list_tables(schemas=["public"])
# Confirms articles, daily_digests tables exist

# Check last article fetch
mcp__supabase__execute_sql(
  query="SELECT MAX(fetched_at) FROM articles"
)
# Shows last fetch was August 10th
```

### Post-Implementation Validation
```python
# Verify articles being fetched
mcp__supabase__execute_sql(
  query="SELECT source, COUNT(*) FROM articles WHERE fetched_at > NOW() - INTERVAL '1 hour' GROUP BY source"
)

# Verify digest generation
mcp__supabase__execute_sql(
  query="SELECT digest_date, total_articles_processed FROM daily_digests ORDER BY created_at DESC LIMIT 1"
)

# Check for any errors
mcp__supabase__get_logs(service="api")
```

## Risk Mitigation
- **Rollback Plan**: Keep Vercel deployment as fallback
- **Secret Security**: Use GitHub's encrypted secrets
- **Cost Control**: Monitor Actions usage, stay under 1000 minutes/month
- **Error Recovery**: CLI scripts have proper error handling and logging
- **Duplicate Prevention**: Concurrency groups prevent overlapping runs

---

**Confidence Score: 9/10**

This implementation has a very high success rate because:
- It reuses existing, tested scheduler functions
- Minimal code changes required (just wrappers and one client modification)
- Clear specification with GPT-5's critical adjustments incorporated
- Comprehensive validation steps at each level
- MCP tools available for verification

The only uncertainty is initial GitHub Secrets configuration, which is straightforward but requires manual setup.