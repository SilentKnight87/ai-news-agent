import pytest
from httpx import AsyncClient
from src.main import app

@pytest.mark.asyncio
async def test_health_endpoint():
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        resp = await ac.get("/api/v1/health")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, dict)

@pytest.mark.asyncio
async def test_articles_endpoint_params():
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        resp = await ac.get("/api/v1/articles", params={"page": 1, "per_page": 5})
    assert resp.status_code in (200, 204, 404)  # tolerate empty datasets locally
