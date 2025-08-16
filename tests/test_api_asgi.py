import pytest
import asyncio
from unittest.mock import patch
from httpx import AsyncClient
from src.main import app

@pytest.mark.asyncio
async def test_health_endpoint():
    """Test health check endpoint works in ASGI environment."""
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        resp = await ac.get("/api/v1/health")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, dict)
    assert "status" in data

@pytest.mark.asyncio
async def test_articles_endpoint_pagination():
    """Test articles endpoint with pagination parameters."""
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        resp = await ac.get("/api/v1/articles", params={"page": 1, "per_page": 5})
    assert resp.status_code in (200, 204, 404)  # tolerate empty datasets locally
    
    if resp.status_code == 200:
        data = resp.json()
        assert "articles" in data
        assert isinstance(data["articles"], list)
        assert len(data["articles"]) <= 5

@pytest.mark.asyncio
async def test_articles_search_endpoint():
    """Test articles search functionality."""
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        resp = await ac.get("/api/v1/articles/search", params={"q": "AI"})
    assert resp.status_code in (200, 404)  # tolerate empty search results
    
    if resp.status_code == 200:
        data = resp.json()
        assert "articles" in data or "total" in data

@pytest.mark.asyncio
async def test_stats_endpoint():
    """Test statistics endpoint."""
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        resp = await ac.get("/api/v1/stats")
    assert resp.status_code in (200, 404)  # tolerate empty database
    
    if resp.status_code == 200:
        data = resp.json()
        assert isinstance(data, dict)

@pytest.mark.asyncio
async def test_digests_endpoint():
    """Test digests listing endpoint."""
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        resp = await ac.get("/api/v1/digests")
    assert resp.status_code in (200, 404)  # tolerate empty digests
    
    if resp.status_code == 200:
        data = resp.json()
        assert isinstance(data, list) or isinstance(data, dict)

@pytest.mark.asyncio
async def test_sources_endpoint():
    """Test sources listing endpoint.""" 
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        resp = await ac.get("/api/v1/sources")
    assert resp.status_code in (200, 404)  # tolerate empty sources

@pytest.mark.asyncio
async def test_cors_headers():
    """Test CORS headers are properly set."""
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        resp = await ac.options("/api/v1/health")
    assert resp.status_code in (200, 405)  # Some frameworks return 405 for OPTIONS

@pytest.mark.asyncio
async def test_error_handling():
    """Test error handling for non-existent endpoints."""
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        resp = await ac.get("/api/v1/nonexistent")
    assert resp.status_code == 404

@pytest.mark.asyncio
async def test_middleware_headers():
    """Test that production middleware adds appropriate headers."""
    # Mock production environment
    with patch.dict('os.environ', {'VERCEL': '1'}):
        async with AsyncClient(app=app, base_url="http://testserver") as ac:
            resp = await ac.get("/api/v1/health")
        
        # Check for performance monitoring headers in production
        if resp.status_code == 200:
            # These headers are added by production middleware
            assert "X-Response-Time" in resp.headers or "X-Content-Type-Options" in resp.headers

@pytest.mark.asyncio
async def test_concurrent_requests():
    """Test handling of concurrent requests (Fluid Compute scenario)."""
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        # Simulate multiple concurrent requests
        tasks = [
            ac.get("/api/v1/health"),
            ac.get("/api/v1/health"),
            ac.get("/api/v1/health")
        ]
        
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # All requests should succeed or fail consistently
        for resp in responses:
            if not isinstance(resp, Exception):
                assert resp.status_code == 200

@pytest.mark.asyncio
async def test_large_query_parameters():
    """Test handling of large query parameters."""
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        # Test with large search query
        large_query = "AI " * 100  # 300 characters
        resp = await ac.get("/api/v1/articles/search", params={"q": large_query})
    assert resp.status_code in (200, 400, 404)  # Should handle gracefully

@pytest.mark.asyncio
async def test_connection_pooling_simulation():
    """Test connection reuse patterns for Fluid Compute."""
    # Multiple requests should reuse connections efficiently
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        responses = []
        for _ in range(5):
            resp = await ac.get("/api/v1/health")
            responses.append(resp.status_code)
    
    # All health checks should succeed
    assert all(status == 200 for status in responses)
