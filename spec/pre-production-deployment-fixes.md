# Pre-Production Deployment Fixes Specification

## Overview
This specification outlines critical issues identified during pre-production audit that must be resolved before deploying the AI News Aggregator to production. The audit was performed on the Backend API (FastAPI), Frontend (Next.js), and MCP Server components.

## Status
- **Priority**: HIGH - Important fixes before production
- **Estimated Time**: 3-4 hours
- **Risk Level**: MEDIUM - Stability issues and some security concerns

## 1. Backend API Critical Issues

### 1.1 Security Vulnerabilities

#### CORS Misconfiguration
- **Location**: `src/main.py:122`
- **Current Issue**: 
  ```python
  allow_origins=["*"]  # Allows any origin
  ```
- **Fix Required**: 
  ```python
  allow_origins=["http://localhost:3000", "https://your-production-domain.com"]
  ```
- **Impact**: Prevents CSRF attacks

#### SQL Injection Vulnerability
- **Location**: `src/repositories/articles.py:534-555`
- **Current Issue**: Unsafe string interpolation in search queries
- **Fix Required**: Use parameterized queries with proper escaping
- **Impact**: Prevents database compromise

#### ✅ Credentials Security (RESOLVED)
- **Location**: `.env` file
- **Status**: **SECURE** - .env file is properly excluded from git
- **Current State**: 
  - `.env` is in .gitignore (line 36)
  - No .env file in git history
  - Only .env.example is tracked
- **Verification**: ✅ API keys are NOT exposed in repository
- **Impact**: No immediate security risk from exposed credentials

### 1.2 Stability Issues

#### Infinite Recursion Bug
- **Location**: `src/api/dependencies.py:90`
- **Current Issue**: Function calls itself indefinitely
- **Fix Required**: Return actual service instance
- **Impact**: Prevents stack overflow crashes

#### Memory Leak in Embeddings Service
- **Location**: `src/services/embeddings.py:34`
- **Current Issue**: Unbounded cache growth
- **Fix Required**: Implement LRU cache with size limits
- **Impact**: Prevents memory exhaustion

#### Database Connection Issues
- **Location**: `src/api/dependencies.py:24`
- **Current Issue**: No connection pooling or retry logic
- **Fix Required**: Implement connection pool with timeout and retry
- **Impact**: Prevents connection exhaustion under load

#### Rate Limiter Hanging
- **Location**: `src/services/rate_limiter.py:86-95`
- **Current Issue**: Waits indefinitely without timeout
- **Fix Required**: Add configurable timeout
- **Impact**: Prevents thread starvation

### 1.3 Missing Features

#### No Authentication System
- **Current Issue**: All API endpoints are public
- **Fix Required**: Implement API key or JWT authentication
- **Impact**: Prevents unauthorized access

#### No Request Validation
- **Current Issue**: No size limits or input validation
- **Fix Required**: Add Pydantic validators and request size limits
- **Impact**: Prevents DoS attacks

## 2. Frontend Critical Issues

### 2.1 Configuration Issues

#### Missing Environment Configuration
- **Location**: `UI/` directory
- **Current Issue**: No `.env.local` or `.env.example`
- **Fix Required**: Create `.env.example`:
  ```env
  NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
  ```
- **Impact**: App fails to connect to production API

### 2.2 Code Issues

#### Broken Authentication Logic
- **Location**: `UI/src/lib/api.ts:29-45`
- **Current Issue**: 
  - Checks for auth_token that's never set
  - Redirects to non-existent `/login` page
- **Fix Required**: Remove authentication code or implement complete flow
- **Impact**: Prevents redirect loops

#### Hardcoded Placeholder Content
- **Location**: `UI/src/components/ArticleModal.tsx:195-207`
- **Current Issue**: Shows fake "Key Points" instead of real data
- **Fix Required**: Display actual article.key_points
- **Impact**: Users see incorrect information

#### Missing Error Boundaries
- **Location**: Main pages (`/`, `/articles`, `/search`, `/digests`)
- **Current Issue**: No error handling for component failures
- **Fix Required**: Wrap pages with ErrorBoundary component
- **Impact**: Prevents white screen crashes

### 2.3 Security Issues

#### Unsafe Image Loading
- **Location**: `UI/next.config.ts:12-13`
- **Current Issue**: Wildcard patterns for image domains
- **Fix Required**: Restrict to specific trusted domains
- **Impact**: Prevents malicious image injection

#### XSS Risk in Article Content
- **Location**: `UI/src/components/ArticleModal.tsx:216`
- **Current Issue**: Unsanitized content rendering
- **Fix Required**: Sanitize article content before display
- **Impact**: Prevents XSS attacks

## 3. Test Suite Issues

### 3.1 Backend Tests
- **Issue**: Pydantic validation errors on startup
- **Error**: Extra fields `github_oauth_client_id` and `github_client_secret`
- **Fix**: Update Settings model or remove extra fields

### 3.2 Frontend Tests
- **Issue**: No test script configured
- **Fix**: Add test script to package.json (lower priority for MVP)

## 4. Repository Cleanup

### 4.1 Files to Remove
```bash
# One-off test scripts
test_production_fetch.py
test_setup.py

# Old test directory
test_ai_news_mcp/

# Large log file (11MB)
logs/app.log

# Build artifacts
UI/tsconfig.tsbuildinfo

# Python cache files
**/__pycache__/
**/*.pyc

# Empty directories (add .gitkeep instead)
audio_outputs/  # Currently empty
```

### 4.2 Directories to Maintain
```bash
# Add .gitkeep to preserve structure
logs/.gitkeep
audio_outputs/.gitkeep
```

## 5. Implementation Plan

### Phase 1: Critical Security (1 hour)
1. Fix CORS configuration
2. Fix SQL injection vulnerability
3. Create .env.example files (Frontend only - Backend already has one)

### Phase 2: Stability Fixes (1-2 hours)
1. Fix infinite recursion bug
2. Implement cache size limits
3. Add database connection pooling
4. Fix rate limiter timeout

### Phase 3: Frontend Fixes (1-2 hours)
1. Create environment configuration
2. Remove/fix authentication code
3. Fix hardcoded content
4. Add error boundaries
5. Restrict image domains

### Phase 4: Cleanup (30 minutes)
1. Remove identified files
2. Add .gitkeep files
3. Update .gitignore

### Phase 5: Validation (30 minutes)
1. Run backend tests
2. Manual frontend testing
3. Security scan

## 6. Post-Deployment Actions

### Immediate Actions
1. Configure production environment variables (no rotation needed - credentials not exposed)
2. Enable monitoring and alerting  
3. Review security headers

### Within 24 Hours
1. Implement authentication system
2. Add request validation
3. Set up rate limiting per user
4. Configure logging and monitoring

## 7. Success Criteria

### Minimum for Production
- [x] No exposed credentials in code (✅ Already secure)
- [ ] CORS properly configured
- [ ] No SQL injection vulnerabilities
- [ ] No infinite loops or memory leaks
- [ ] Frontend connects to correct API
- [ ] Error boundaries prevent crashes
- [ ] All critical tests pass

### Recommended Additions
- [ ] Authentication implemented
- [ ] Rate limiting configured
- [ ] Monitoring enabled
- [ ] Security headers added
- [ ] Input validation complete

## 8. Risk Assessment

### Without These Fixes
- **Security Risk**: MEDIUM - CORS and SQL injection vulnerabilities
- **Stability Risk**: HIGH - Application crashes likely
- **Data Risk**: MEDIUM - Database compromise possible via injection
- **User Experience**: POOR - Crashes and incorrect data

### After Implementation
- **Security Risk**: LOW - Major vulnerabilities resolved
- **Stability Risk**: LOW - Crash-causing bugs fixed
- **Data Risk**: LOW - Injection attacks prevented
- **User Experience**: GOOD - Stable and functional

## 9. Testing Requirements

### Backend Testing
```bash
# Run all tests
pytest tests/ -v

# Security scan
bandit -r src/

# Check for secrets
trufflehog filesystem ./
```

### Frontend Testing
```bash
# Build check
npm run build

# Type checking
npm run type-check

# Manual testing checklist
- [ ] All pages load without errors
- [ ] API calls work correctly
- [ ] Error states handled gracefully
- [ ] No console errors in browser
```

## 10. Documentation Updates

### Required Updates
1. Update README.md with security best practices
2. Create SECURITY.md with vulnerability reporting
3. Document environment variables in .env.example
4. Update deployment guides with security steps

## Conclusion

These fixes address critical security vulnerabilities and stability issues that would prevent safe production deployment. The implementation should be completed in priority order, with security fixes taking precedence. After implementation, the application will meet minimum viable product (MVP) requirements for production deployment.

**Total Estimated Time**: 3-4 hours
**Recommended Team**: 1 developer with basic security review
**Deployment Readiness**: Ready to deploy after fixing stability and security issues (credentials already secure)