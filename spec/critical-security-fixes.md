# Critical Security Fixes for Pre-Production Deployment

**Priority:** CRITICAL  
**Status:** Implementation Required  
**Target:** Must be completed before production deployment  
**Date:** 2025-08-13

## Executive Summary

This specification addresses 5 critical security vulnerabilities identified in the AI News Aggregator that must be resolved before production deployment. These issues represent immediate security risks that could lead to data breaches, resource exhaustion, or unauthorized access.

## Critical Issues Overview

| Issue | Severity | Impact | Exploitability |
|-------|----------|---------|----------------|
| Unauthenticated Operational Endpoints | CRITICAL | DoS, Resource Exhaustion | HIGH |
| SSRF in Audio Streaming | CRITICAL | Internal Network Access | HIGH |
| Missing Supabase Service Role | CRITICAL | Write Operations Failure | HIGH |
| Database Security Gaps | CRITICAL | Data Exposure | MEDIUM |
| HTTP Client Vulnerabilities | HIGH | Resource Exhaustion | MEDIUM |

## 1. Unauthenticated Operational Endpoints

### Problem
The endpoints `/webhook/fetch` and `/scheduler/task/{task_name}/run` are publicly accessible without authentication, allowing anyone to trigger expensive background operations.

### Risk
- **Resource Exhaustion:** Attackers can trigger unlimited fetch operations
- **Cost Amplification:** Excessive API calls to external services
- **DoS Potential:** Overload background task queue

### Implementation Requirements

#### 1.1 API Key Authentication
```python
# src/config.py - Add configuration
api_keys: str = Field("", description="Comma-separated list of valid API keys")

# src/api/auth.py - Create authentication dependency
async def verify_api_key(x_api_key: str = Header(None)) -> bool:
    if not x_api_key:
        raise HTTPException(401, "API key required")
    
    settings = get_settings()
    valid_keys = [k.strip() for k in settings.api_keys.split(",") if k.strip()]
    
    if x_api_key not in valid_keys:
        raise HTTPException(403, "Invalid API key")
    
    return True
```

#### 1.2 Protect Endpoints
```python
# src/api/routes.py - Update endpoints
@router.post("/webhook/fetch", dependencies=[Depends(verify_api_key)])
async def trigger_fetch(...)

@router.post("/scheduler/task/{task_name}/run", dependencies=[Depends(verify_api_key)])
async def run_scheduler_task(...)
```

#### 1.3 Environment Configuration
```bash
# .env.example - Add API keys
OPERATIONAL_API_KEYS=your_api_key_1,your_api_key_2
```

## 2. SSRF Protection for Audio Streaming

### Problem
`stream_audio_content()` accepts arbitrary URLs without validation, enabling Server-Side Request Forgery attacks against internal services.

### Risk
- **Internal Network Scanning:** Access to localhost/private IPs
- **Cloud Metadata Access:** AWS/GCP instance metadata endpoints
- **Service Discovery:** Enumerate internal services

### Implementation Requirements

#### 2.1 URL Validation Function
```python
# src/services/security.py - Create security utilities
import ipaddress
from urllib.parse import urlparse

ALLOWED_AUDIO_HOSTS = [
    "supabase.co",
    "cdn.supabase.co", 
    # Add your storage domain
]

BLOCKED_IP_RANGES = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),  # AWS metadata
]

async def validate_audio_url(url: str) -> bool:
    parsed = urlparse(url)
    
    # Only allow HTTPS
    if parsed.scheme != "https":
        return False
    
    # Check host allowlist
    if parsed.hostname not in ALLOWED_AUDIO_HOSTS:
        return False
    
    # Resolve DNS and check IP ranges
    try:
        import socket
        ip = socket.gethostbyname(parsed.hostname)
        for blocked_range in BLOCKED_IP_RANGES:
            if ipaddress.ip_address(ip) in blocked_range:
                return False
    except:
        return False
    
    return True
```

#### 2.2 Update Audio Streaming
```python
# src/api/audio.py - Add validation
async def stream_audio_content(url: str, chunk_size: int = 8192):
    if not await validate_audio_url(url):
        raise HTTPException(403, "URL not allowed")
    
    # Continue with existing logic...
```

## 3. Supabase Service Role Configuration

### Problem
Backend is configured to use `supabase_anon_key` but RLS policies require `service_role` for write operations, causing all writes to fail.

### Risk
- **Application Failure:** Cannot create/update articles or digests
- **Data Integrity:** Partial operations may leave inconsistent state

### Implementation Requirements

#### 3.1 Environment Configuration
```bash
# .env.example - Add service role key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key_here
```

#### 3.2 Configuration Update
```python
# src/config.py - Add service role key
supabase_service_role_key: str = Field("", description="Supabase service role key for backend operations")
```

#### 3.3 Client Factory Update
```python
# src/api/dependencies.py - Create role-specific clients
@lru_cache
def get_supabase_service_client() -> Client:
    """Get Supabase client with service role for write operations."""
    settings = get_settings()
    
    if not settings.supabase_service_role_key:
        raise ValueError("SUPABASE_SERVICE_ROLE_KEY is required for backend operations")
    
    client = create_client(
        settings.supabase_url,
        settings.supabase_service_role_key,
        options=ClientOptions(...)
    )
    return client

def get_article_repository_write(
    supabase: Annotated[Client, Depends(get_supabase_service_client)]
) -> ArticleRepository:
    """Get article repository with write permissions."""
    return ArticleRepository(supabase)
```

#### 3.4 Update Write Operations
```python
# src/api/routes.py - Use service client for writes
@router.post("/webhook/fetch")
async def trigger_fetch(
    article_repo: Annotated[ArticleRepository, Depends(get_article_repository_write)]
):
    # Use write-enabled repository...
```

## 4. Database Security Audit

### Problem
Database schema may have security vulnerabilities that could expose data or allow unauthorized access.

### Risk
- **Data Exposure:** Missing RLS policies
- **Unauthorized Access:** Overly permissive policies
- **Data Corruption:** Missing constraints

### Implementation Requirements

#### 4.1 Automated Security Scan
```python
# Use Supabase MCP tools to audit
# Check security advisors
# Verify RLS policies
# Review table permissions
```

#### 4.2 Manual Schema Review
- Verify all tables have RLS enabled
- Check policy coverage for all operations
- Validate foreign key constraints
- Review stored function security

## 5. HTTP Client Standardization

### Problem
Inconsistent timeout handling and missing error checking can cause hanging connections and silent failures.

### Risk
- **Resource Exhaustion:** Hanging HTTP connections
- **Silent Failures:** Errors not properly handled
- **Service Degradation:** Cascading timeout issues

### Implementation Requirements

#### 5.1 Standard HTTP Configuration
```python
# src/services/http_client.py - Create standard client
import httpx

def get_standard_http_client() -> httpx.AsyncClient:
    timeout = httpx.Timeout(
        connect=5.0,
        read=30.0,
        write=10.0,
        pool=5.0
    )
    
    limits = httpx.Limits(
        max_keepalive_connections=5,
        max_connections=10
    )
    
    return httpx.AsyncClient(
        timeout=timeout,
        limits=limits,
        follow_redirects=True
    )
```

#### 5.2 Update All HTTP Calls
- Replace all httpx usage with standard client
- Add `response.raise_for_status()` calls
- Implement proper error handling

## Implementation Priority

1. **IMMEDIATE:** Supabase service role configuration (fixes write failures)
2. **IMMEDIATE:** SSRF protection (prevents internal network access)
3. **IMMEDIATE:** Operational endpoint authentication (prevents DoS)
4. **HIGH:** Database security audit (validates current security posture)
5. **HIGH:** HTTP client standardization (prevents resource exhaustion)

## Validation Criteria

### Security Tests
- [ ] Operational endpoints reject requests without valid API key
- [ ] Audio streaming rejects non-allowlisted URLs
- [ ] Write operations work with service role client
- [ ] All HTTP clients have proper timeout configuration
- [ ] Database audit shows no critical security issues

### Functional Tests
- [ ] Article creation/update operations succeed
- [ ] Digest generation completes successfully
- [ ] Audio streaming works for valid URLs
- [ ] Background tasks execute properly
- [ ] All endpoints return appropriate error codes

## Post-Deployment Monitoring

- Monitor operational endpoint access patterns
- Alert on unusual audio URL requests
- Track database operation success rates
- Monitor HTTP client timeout patterns
- Log all authentication failures

## Emergency Response

If security issues are discovered in production:
1. Immediately disable affected endpoints via feature flags
2. Review access logs for signs of exploitation
3. Apply emergency patches and redeploy
4. Conduct full security review of codebase