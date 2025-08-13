# PRP: Critical Security Fixes for Pre-Production Deployment

**Feature:** Critical Security Vulnerability Mitigation  
**Priority:** CRITICAL  
**Confidence Score:** 9/10  
**Date:** 2025-08-13  
**Source Spec:** spec/critical-security-fixes.md

## Executive Summary

This PRP addresses 5 critical security vulnerabilities that must be resolved before production deployment. These issues present immediate risks including DoS attacks, SSRF exploitation, data breaches, and service failures. The implementation follows defense-in-depth principles with multiple security layers.

## Pre-Implementation Research Phase

### 1. MCP Tool Research Commands

```bash
# Get latest FastAPI security docs
mcp__context7__resolve-library-id("fastapi")
mcp__context7__get-library-docs("/tiangolo/fastapi", topic="security api_key dependencies authentication")

# Get httpx configuration docs  
mcp__context7__resolve-library-id("httpx")
mcp__context7__get-library-docs("/encode/httpx", topic="timeout limits AsyncClient configuration")

# Check current database security
mcp__supabase__list_tables(schemas=["public"])
mcp__supabase__get_advisors(type="security")
```

### 2. Current State Analysis

The codebase analysis reveals:
- **Vulnerable Endpoints:** `/webhook/fetch` and `/scheduler/task/{task_name}/run` have no authentication
- **SSRF Risk:** `stream_audio_content()` in `src/api/audio.py` accepts arbitrary URLs
- **Missing Configuration:** No service role key configured for Supabase write operations
- **Database Issues:** RLS disabled on `audio_processing_queue` table (discovered via MCP)
- **HTTP Client Issues:** No standardized timeout configuration across fetchers

## Implementation Blueprint

### Issue 1: Unauthenticated Operational Endpoints

#### 1.1 Create Authentication Module
```python
# src/api/auth.py
from typing import Annotated
from fastapi import Depends, HTTPException, Header, status
from ..config import get_settings
import secrets
import logging

logger = logging.getLogger(__name__)

async def verify_api_key(x_api_key: Annotated[str | None, Header()] = None) -> bool:
    """
    Verify API key for operational endpoints.
    
    Uses constant-time comparison to prevent timing attacks.
    """
    if not x_api_key:
        logger.warning("Missing API key in request")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    settings = get_settings()
    if not settings.operational_api_keys:
        logger.error("No API keys configured")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API authentication not configured"
        )
    
    # Parse comma-separated keys
    valid_keys = [k.strip() for k in settings.operational_api_keys.split(",") if k.strip()]
    
    # Use constant-time comparison
    is_valid = any(secrets.compare_digest(x_api_key, key) for key in valid_keys)
    
    if not is_valid:
        logger.warning(f"Invalid API key attempt")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key"
        )
    
    return True
```

#### 1.2 Update Configuration
```python
# src/config.py - Add to Settings class
operational_api_keys: str = Field(
    "", 
    description="Comma-separated list of valid API keys for operational endpoints"
)
```

#### 1.3 Protect Endpoints
```python
# src/api/routes.py - Update imports
from .auth import verify_api_key

# Update endpoints
@router.post("/webhook/fetch", response_model=FetchTriggerResponse, dependencies=[Depends(verify_api_key)])
async def trigger_fetch(...)

@router.post("/scheduler/task/{task_name}/run", dependencies=[Depends(verify_api_key)])
async def run_scheduler_task(...)
```

### Issue 2: SSRF Protection for Audio Streaming

#### 2.1 Create Security Module
```python
# src/services/security.py
import ipaddress
import socket
import logging
from urllib.parse import urlparse
from typing import Optional

logger = logging.getLogger(__name__)

# Configuration
ALLOWED_AUDIO_HOSTS = [
    "supabase.co",
    "cdn.supabase.co",
    "supabase.in",  # Add your specific Supabase domain
]

BLOCKED_IP_RANGES = [
    ipaddress.ip_network("10.0.0.0/8"),       # Private
    ipaddress.ip_network("172.16.0.0/12"),    # Private
    ipaddress.ip_network("192.168.0.0/16"),   # Private
    ipaddress.ip_network("127.0.0.0/8"),      # Loopback
    ipaddress.ip_network("169.254.0.0/16"),   # Link-local
    ipaddress.ip_network("::1/128"),          # IPv6 loopback
    ipaddress.ip_network("fc00::/7"),         # IPv6 private
]

async def validate_audio_url(url: str) -> bool:
    """
    Validate URL for audio streaming to prevent SSRF attacks.
    
    Args:
        url: URL to validate
        
    Returns:
        bool: True if URL is safe, False otherwise
    """
    try:
        parsed = urlparse(url)
        
        # 1. Only allow HTTPS
        if parsed.scheme != "https":
            logger.warning(f"Rejected non-HTTPS URL: {url}")
            return False
        
        # 2. Check hostname exists
        if not parsed.hostname:
            logger.warning(f"Rejected URL without hostname: {url}")
            return False
        
        # 3. Check against allowlist
        hostname = parsed.hostname.lower()
        if not any(hostname.endswith(allowed) for allowed in ALLOWED_AUDIO_HOSTS):
            logger.warning(f"Rejected non-allowlisted host: {hostname}")
            return False
        
        # 4. Resolve DNS and check IP ranges
        try:
            # Get all IP addresses for the hostname
            addr_info = socket.getaddrinfo(hostname, None)
            ips = set()
            
            for info in addr_info:
                ip_str = info[4][0]
                ips.add(ip_str)
            
            # Check each resolved IP
            for ip_str in ips:
                try:
                    ip_addr = ipaddress.ip_address(ip_str)
                    
                    # Check against blocked ranges
                    for blocked_range in BLOCKED_IP_RANGES:
                        if ip_addr in blocked_range:
                            logger.warning(f"Rejected IP in blocked range: {ip_str}")
                            return False
                            
                except ValueError:
                    logger.error(f"Invalid IP address: {ip_str}")
                    return False
                    
        except socket.gaierror as e:
            logger.error(f"DNS resolution failed for {hostname}: {e}")
            return False
        
        logger.debug(f"Validated audio URL: {url}")
        return True
        
    except Exception as e:
        logger.error(f"URL validation error: {e}")
        return False

def get_allowed_hosts() -> list[str]:
    """Get list of allowed audio hosts for documentation."""
    return ALLOWED_AUDIO_HOSTS.copy()
```

#### 2.2 Update Audio Streaming
```python
# src/api/audio.py - Update imports
from ..services.security import validate_audio_url

# Update stream_audio_content function
async def stream_audio_content(url: str, chunk_size: int = 8192) -> AsyncGenerator[bytes, None]:
    """
    Stream audio content from validated URL.
    """
    # Validate URL first
    if not await validate_audio_url(url):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="URL not allowed for audio streaming"
        )
    
    # Use timeout configuration
    timeout = httpx.Timeout(
        connect=5.0,
        read=30.0,
        write=10.0,
        pool=5.0
    )
    
    async with httpx.AsyncClient(timeout=timeout) as client:
        async with client.stream("GET", url) as response:
            response.raise_for_status()
            async for chunk in response.aiter_bytes(chunk_size):
                yield chunk
```

### Issue 3: Supabase Service Role Configuration

#### 3.1 Update Configuration
```python
# src/config.py - Add to Settings class
supabase_service_role_key: str = Field(
    "",
    description="Supabase service role key for backend write operations"
)
```

#### 3.2 Create Service Client Factory
```python
# src/api/dependencies.py - Add new functions
from functools import lru_cache
from supabase.lib.client_options import ClientOptions

@lru_cache
def get_supabase_service_client() -> Client:
    """
    Get Supabase client with service role for write operations.
    
    This client bypasses RLS and should only be used for
    backend operations that require elevated privileges.
    """
    settings = get_settings()
    
    if not settings.supabase_service_role_key:
        raise ValueError(
            "SUPABASE_SERVICE_ROLE_KEY is required for backend operations. "
            "Please set it in your environment variables."
        )
    
    # Configure with service role
    options = ClientOptions(
        schema="public",
        headers={
            "x-application": "ai-news-aggregator-backend",
            "x-service-role": "true"
        },
        auto_refresh_token=True,
        persist_session=True,
        storage={},
        flow_type="implicit"
    )
    
    client = create_client(
        settings.supabase_url,
        settings.supabase_service_role_key,
        options=options
    )
    
    logger.info("Created Supabase service client for write operations")
    return client

def get_article_repository_write(
    supabase: Annotated[Client, Depends(get_supabase_service_client)]
) -> ArticleRepository:
    """Get article repository with write permissions."""
    return ArticleRepository(supabase)

def get_deduplication_service_write(
    supabase: Annotated[Client, Depends(get_supabase_service_client)]
) -> DeduplicationService:
    """Get deduplication service with write permissions."""
    return DeduplicationService(supabase)
```

#### 3.3 Update Write Operations
```python
# src/api/routes.py - Update write endpoints
@router.post("/webhook/fetch", response_model=FetchTriggerResponse, dependencies=[Depends(verify_api_key)])
async def trigger_fetch(
    request: FetchTriggerRequest,
    background_tasks: BackgroundTasks,
    article_repo: Annotated[ArticleRepository, Depends(get_article_repository_write)],  # Changed
    deduplication_service: Annotated[DeduplicationService, Depends(get_deduplication_service_write)],  # Changed
    news_analyzer: Annotated[NewsAnalyzer, Depends(get_news_analyzer)]
) -> FetchTriggerResponse:
    # ... existing code
```

### Issue 4: Database Security Fixes

#### 4.1 Enable RLS on audio_processing_queue
```sql
-- Migration: enable_audio_queue_rls.sql
-- Enable RLS on audio_processing_queue table
ALTER TABLE public.audio_processing_queue ENABLE ROW LEVEL SECURITY;

-- Create policy for service role (full access)
CREATE POLICY "Service role has full access to audio_processing_queue"
ON public.audio_processing_queue
FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

-- Create policy for authenticated users (read only)
CREATE POLICY "Authenticated users can read audio_processing_queue"
ON public.audio_processing_queue
FOR SELECT
TO authenticated
USING (true);
```

#### 4.2 Move vector extension
```sql
-- Migration: move_vector_extension.sql
-- Create extensions schema if not exists
CREATE SCHEMA IF NOT EXISTS extensions;

-- Move vector extension to extensions schema
ALTER EXTENSION vector SET SCHEMA extensions;

-- Update search path for functions using vector
ALTER FUNCTION public.match_articles SET search_path = public, extensions;
```

#### 4.3 Fix function search paths
```sql
-- Migration: fix_function_search_paths.sql
-- Fix search_path for get_top_articles_for_digest
ALTER FUNCTION public.get_top_articles_for_digest 
SET search_path = public, extensions;

-- Fix search_path for match_articles
ALTER FUNCTION public.match_articles 
SET search_path = public, extensions;
```

### Issue 5: HTTP Client Standardization

#### 5.1 Create Standard HTTP Client
```python
# src/services/http_client.py
import httpx
from typing import Optional
import logging

logger = logging.getLogger(__name__)

def get_standard_http_client(
    timeout_seconds: float = 30.0,
    max_keepalive: int = 5,
    max_connections: int = 10
) -> httpx.AsyncClient:
    """
    Create a standardized HTTP client with proper timeouts and limits.
    
    Args:
        timeout_seconds: Total timeout for requests
        max_keepalive: Maximum keepalive connections
        max_connections: Maximum total connections
        
    Returns:
        Configured AsyncClient instance
    """
    # Configure timeouts
    timeout = httpx.Timeout(
        connect=5.0,          # Connection timeout
        read=timeout_seconds, # Read timeout
        write=10.0,          # Write timeout
        pool=5.0             # Pool timeout
    )
    
    # Configure connection limits
    limits = httpx.Limits(
        max_keepalive_connections=max_keepalive,
        max_connections=max_connections,
        keepalive_expiry=5.0
    )
    
    # Create client with standard configuration
    client = httpx.AsyncClient(
        timeout=timeout,
        limits=limits,
        follow_redirects=False,  # Don't follow redirects automatically
        http2=True,              # Enable HTTP/2
        headers={
            "User-Agent": "AI-News-Aggregator/1.0"
        }
    )
    
    logger.debug(f"Created standard HTTP client with {timeout_seconds}s timeout")
    return client

def get_fetcher_http_client(source: str) -> httpx.AsyncClient:
    """
    Get HTTP client configured for specific fetcher.
    
    Args:
        source: Source name for customization
        
    Returns:
        Configured AsyncClient for fetcher
    """
    # Customize per source if needed
    timeout_map = {
        "arxiv": 60.0,      # ArXiv can be slow
        "github": 30.0,
        "reddit": 30.0,
        "hackernews": 20.0
    }
    
    timeout = timeout_map.get(source.lower(), 30.0)
    return get_standard_http_client(timeout_seconds=timeout)
```

#### 5.2 Update Fetchers
```python
# src/fetchers/base.py - Update RateLimitedHTTPClient
class RateLimitedHTTPClient:
    def __init__(self, requests_per_second: float = 1.0, max_retries: int = 3):
        self.delay = 1.0 / requests_per_second
        self.max_retries = max_retries
        self._last_request_time: datetime | None = None
        # Use standard client
        from ..services.http_client import get_standard_http_client
        self.client = get_standard_http_client()

    async def get(self, url: str, **kwargs) -> Any:
        # Apply rate limiting
        await self._apply_rate_limit()
        
        for attempt in range(self.max_retries + 1):
            try:
                response = await self.client.get(url, **kwargs)
                response.raise_for_status()
                return response
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:
                    # Handle rate limiting with exponential backoff
                    delay = (2 ** attempt) + random.uniform(0.1, 0.3)
                    logger.warning(f"Rate limited, retrying in {delay:.2f}s")
                    await asyncio.sleep(delay)
                    continue
                raise FetchError(f"HTTP error {e.response.status_code}: {e}")
            except httpx.TimeoutException as e:
                logger.error(f"Request timeout: {e}")
                raise FetchError(f"Request timed out: {e}")
            except Exception as e:
                if attempt == self.max_retries:
                    raise FetchError(f"Request failed after {self.max_retries} retries: {e}")
                delay = (2 ** attempt) + random.uniform(0.1, 0.3)
                await asyncio.sleep(delay)
```

## MCP Tool Integration

### Database Operations

```python
# Apply migrations using Supabase MCP
async def apply_security_migrations():
    """Apply all security-related database migrations."""
    
    # 1. Enable RLS on audio_processing_queue
    await mcp__supabase__apply_migration(
        name="enable_audio_queue_rls",
        query="""
        ALTER TABLE public.audio_processing_queue ENABLE ROW LEVEL SECURITY;
        
        CREATE POLICY "Service role has full access"
        ON public.audio_processing_queue
        FOR ALL TO service_role
        USING (true) WITH CHECK (true);
        """
    )
    
    # 2. Move vector extension
    await mcp__supabase__apply_migration(
        name="move_vector_extension",
        query="""
        CREATE SCHEMA IF NOT EXISTS extensions;
        ALTER EXTENSION vector SET SCHEMA extensions;
        """
    )
    
    # 3. Fix function search paths
    await mcp__supabase__apply_migration(
        name="fix_function_search_paths",
        query="""
        ALTER FUNCTION public.get_top_articles_for_digest 
        SET search_path = public, extensions;
        
        ALTER FUNCTION public.match_articles 
        SET search_path = public, extensions;
        """
    )
```

### Validation and Testing

```python
# Test API key authentication
async def test_api_key_auth():
    """Test that operational endpoints require API keys."""
    
    # Test without API key
    response = await client.post("/webhook/fetch")
    assert response.status_code == 401
    
    # Test with invalid key
    response = await client.post(
        "/webhook/fetch",
        headers={"X-API-Key": "invalid"}
    )
    assert response.status_code == 403
    
    # Test with valid key
    response = await client.post(
        "/webhook/fetch",
        headers={"X-API-Key": os.getenv("TEST_API_KEY")},
        json={"sources": ["arxiv"]}
    )
    assert response.status_code == 200

# Test SSRF protection
async def test_ssrf_protection():
    """Test that audio streaming blocks malicious URLs."""
    
    test_cases = [
        ("http://example.com/audio.mp3", 403),  # Non-HTTPS
        ("https://169.254.169.254/", 403),      # AWS metadata
        ("https://localhost/audio.mp3", 403),    # Localhost
        ("https://192.168.1.1/", 403),          # Private IP
        ("https://evil.com/audio.mp3", 403),    # Non-allowlisted
    ]
    
    for url, expected_status in test_cases:
        response = await client.get(
            f"/digests/test-id/audio",
            params={"url": url}
        )
        assert response.status_code == expected_status
```

## Validation Gates

### Pre-Deployment Checklist

```bash
# 1. Syntax and style check
ruff check --fix src/
mypy src/

# 2. Run unit tests
pytest tests/test_auth.py -v
pytest tests/test_security.py -v
pytest tests/test_http_client.py -v

# 3. Check database security with MCP
mcp__supabase__get_advisors(type="security")
# Should return no CRITICAL or ERROR level issues

# 4. Verify RLS is enabled
mcp__supabase__execute_sql(query="""
    SELECT tablename, rowsecurity 
    FROM pg_tables 
    WHERE schemaname = 'public'
""")
# All tables should have rowsecurity = true

# 5. Test endpoints manually
curl -X POST http://localhost:8000/webhook/fetch
# Should return 401

curl -X POST http://localhost:8000/webhook/fetch \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"sources": ["arxiv"]}'
# Should return 200

# 6. Load test with rate limiting
hey -n 1000 -c 10 -H "X-API-Key: $API_KEY" \
  http://localhost:8000/webhook/fetch
# Should handle without errors

# 7. Security scan
bandit -r src/ -ll
# Should return no high severity issues
```

### Post-Deployment Monitoring

```python
# Monitor authentication failures
mcp__supabase__get_logs(service="api")
# Check for 401/403 responses

# Monitor SSRF blocks
grep "Rejected" logs/security.log | tail -100
# Review blocked URL attempts

# Check database advisors
mcp__supabase__get_advisors(type="security")
# Ensure no new issues
```

## Environment Configuration

```bash
# .env.example additions
# API Keys (generate with: openssl rand -hex 32)
OPERATIONAL_API_KEYS=key1_here,key2_here

# Supabase Service Role (from Supabase dashboard)
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key_here

# Security settings
ALLOWED_AUDIO_HOSTS=supabase.co,cdn.supabase.co
MAX_REQUEST_TIMEOUT=30
ENABLE_SECURITY_LOGS=true
```

## Rollback Plan

If issues occur after deployment:

1. **Revert code changes:**
   ```bash
   git revert HEAD~5..HEAD
   git push origin main
   ```

2. **Rollback database migrations:**
   ```sql
   -- Disable RLS if causing issues
   ALTER TABLE public.audio_processing_queue DISABLE ROW LEVEL SECURITY;
   
   -- Move vector extension back if needed
   ALTER EXTENSION vector SET SCHEMA public;
   ```

3. **Restore previous configuration:**
   - Remove API key requirements from endpoints
   - Disable URL validation temporarily
   - Switch back to anon key for all operations

## Success Metrics

- **Zero** unauthenticated access to operational endpoints
- **Zero** successful SSRF attempts in logs
- **100%** of write operations succeed with service role
- **All** database tables have RLS enabled
- **All** HTTP requests complete within timeout
- **<1%** error rate on protected endpoints
- **<100ms** added latency from security checks

## MCP Tool Usage Summary

1. **Supabase MCP:**
   - Apply migrations for RLS and extension fixes
   - Run security advisors to validate configuration
   - Monitor logs for security events
   
2. **Context7 MCP:**
   - Retrieve latest FastAPI security patterns
   - Get httpx timeout configuration docs
   
3. **IDE/Testing MCP:**
   - Run ruff and mypy for code validation
   - Execute pytest for security tests

## Confidence Score Justification: 9/10

- **+2:** Comprehensive research using MCP tools
- **+2:** Defense-in-depth approach with multiple layers
- **+2:** Industry-standard security practices (API keys, SSRF protection)
- **+2:** Detailed validation gates and rollback plan
- **+1:** Clear success metrics and monitoring
- **-1:** Some complexity in service role migration may require careful testing

This PRP provides a production-ready security implementation that addresses all critical vulnerabilities while maintaining system functionality and performance.