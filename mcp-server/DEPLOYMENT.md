# 🚀 Production Deployment Guide

## Critical Pre-Deployment Steps (REQUIRED)

### 1. Create KV Namespace for Caching

**CRITICAL**: The application will fail silently without this step - caching will not work.

```bash
# Login to Cloudflare (if not already done)
npx wrangler login

# Create the CACHE KV namespace
npx wrangler kv namespace create "CACHE"
```

This will output something like:
```
{ binding = "CACHE", id = "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6" }
```

### 2. Update wrangler.jsonc with Real KV Namespace ID

Replace the placeholder in `wrangler.jsonc`:

```json
"kv_namespaces": [
  {
    "binding": "OAUTH_KV",
    "id": "06998ca39ffb4273a10747065041347b"
  },
  {
    "binding": "CACHE",
    "id": "REPLACE_WITH_ACTUAL_ID_FROM_STEP_1"
  }
]
```

### 3. Set Environment Variables

```bash
# Set required secrets
npx wrangler secret put DATABASE_URL
npx wrangler secret put GITHUB_CLIENT_ID  
npx wrangler secret put GITHUB_CLIENT_SECRET
npx wrangler secret put COOKIE_ENCRYPTION_KEY
npx wrangler secret put SUPABASE_URL
npx wrangler secret put SUPABASE_ANON_KEY
```

### 4. Deploy to Production

```bash
npx wrangler deploy
```

## ✅ Deployment Verification

After deployment, verify the following:

1. **Cache is working**: Check if search results are cached on repeat queries
2. **Database connectivity**: Ensure all 6 news tools respond correctly
3. **OAuth flow**: Test GitHub authentication works
4. **Error handling**: Verify tools return proper error messages

## 🎯 MCP Inspector Testing

Test the deployed server with MCP Inspector:

```bash
# Test with production URL
npx @modelcontextprotocol/inspector@latest https://your-worker.workers.dev/mcp
```

Test each tool:
- `search_articles` - Search functionality with caching
- `get_latest_articles` - Recent articles retrieval  
- `get_article_stats` - Database statistics
- `get_digests` - Daily digest pagination
- `get_digest_by_id` - Individual digest retrieval
- `get_sources` - News source metadata

## 🔧 Troubleshooting

### Cache Not Working
- Verify CACHE KV namespace exists and ID is correct in wrangler.jsonc
- Check environment variables are set correctly

### Database Errors  
- Verify DATABASE_URL uses pooled connection (port 6543 for Supabase)
- Check database connectivity and credentials

### Auth Issues
- Verify GitHub OAuth app is configured correctly
- Check GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET are set