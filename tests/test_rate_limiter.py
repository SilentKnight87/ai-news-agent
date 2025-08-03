"""
Tests for rate limiting service.
"""

import asyncio
import time

import pytest

from src.services.rate_limiter import (
    RateLimitConfig,
    RateLimiter,
    ServiceRateLimitManager,
    get_rate_limit_manager,
    rate_limited_request,
)


class TestRateLimiter:
    """Test the RateLimiter class."""

    def test_rate_limit_config(self):
        """Test rate limit configuration."""
        config = RateLimitConfig(
            requests_per_second=2.0,
            burst_limit=5,
            cooldown_seconds=10.0
        )

        assert config.requests_per_second == 2.0
        assert config.burst_limit == 5
        assert config.cooldown_seconds == 10.0

    @pytest.mark.asyncio
    async def test_rate_limiter_acquire(self):
        """Test token acquisition."""
        config = RateLimitConfig(requests_per_second=10.0, burst_limit=5)
        limiter = RateLimiter(config)

        # Should be able to acquire up to burst limit immediately
        for _ in range(5):
            assert await limiter.acquire() is True

        # Should be rate limited after burst
        assert await limiter.acquire() is False

    @pytest.mark.asyncio
    async def test_rate_limiter_token_replenishment(self):
        """Test that tokens are replenished over time."""
        config = RateLimitConfig(requests_per_second=10.0, burst_limit=2)
        limiter = RateLimiter(config)

        # Exhaust tokens
        assert await limiter.acquire() is True
        assert await limiter.acquire() is True
        assert await limiter.acquire() is False

        # Wait for token replenishment
        await asyncio.sleep(0.3)  # Should get ~3 tokens back
        assert await limiter.acquire() is True

    @pytest.mark.asyncio
    async def test_rate_limiter_wait_for_tokens(self):
        """Test waiting for tokens."""
        config = RateLimitConfig(requests_per_second=5.0, burst_limit=1)
        limiter = RateLimiter(config)

        # Exhaust tokens
        assert await limiter.acquire() is True

        # This should wait and then succeed
        start_time = time.time()
        await limiter.wait_for_tokens()
        elapsed = time.time() - start_time

        # Should have waited at least 0.1 seconds (1/10 req/s with some margin)
        assert elapsed >= 0.1

    def test_rate_limiter_status(self):
        """Test rate limiter status reporting."""
        config = RateLimitConfig(requests_per_second=2.0, burst_limit=10)
        limiter = RateLimiter(config)

        status = limiter.get_status()

        assert "available_tokens" in status
        assert "max_tokens" in status
        assert "requests_per_second" in status
        assert "utilization" in status
        assert status["max_tokens"] == 10
        assert status["requests_per_second"] == 2.0


class TestServiceRateLimitManager:
    """Test the ServiceRateLimitManager class."""

    def test_manager_initialization(self):
        """Test manager initialization with default services."""
        manager = ServiceRateLimitManager()

        # Should have default services
        expected_services = ["arxiv", "hackernews", "rss", "gemini", "elevenlabs"]
        for service in expected_services:
            assert service in manager.limiters

    @pytest.mark.asyncio
    async def test_service_rate_limiting(self):
        """Test service-specific rate limiting."""
        manager = ServiceRateLimitManager()

        # ArXiv should be more restrictive than HackerNews
        arxiv_acquired = await manager.acquire("arxiv", 1)
        hn_acquired = await manager.acquire("hackernews", 1)

        assert arxiv_acquired is True
        assert hn_acquired is True

        # Check that ArXiv is more restrictive (smaller burst)
        arxiv_status = manager.get_service_stats("arxiv")
        hn_status = manager.get_service_stats("hackernews")

        arxiv_burst = arxiv_status["rate_limit_status"]["max_tokens"]
        hn_burst = hn_status["rate_limit_status"]["max_tokens"]

        assert arxiv_burst < hn_burst

    @pytest.mark.asyncio
    async def test_unknown_service_default(self):
        """Test that unknown services get default rate limiting."""
        manager = ServiceRateLimitManager()

        # Should create default limiter for unknown service
        assert await manager.acquire("unknown_service") is True

        # Should now be tracked
        assert "unknown_service" in manager.limiters

    def test_add_custom_service(self):
        """Test adding custom service rate limiting."""
        manager = ServiceRateLimitManager()

        custom_config = RateLimitConfig(
            requests_per_second=5.0,
            burst_limit=20,
            cooldown_seconds=30.0
        )

        manager.add_service("custom_api", custom_config)

        assert "custom_api" in manager.limiters
        status = manager.get_service_stats("custom_api")
        assert status["rate_limit_status"]["max_tokens"] == 20

    @pytest.mark.asyncio
    async def test_wait_and_acquire(self):
        """Test waiting for tokens."""
        manager = ServiceRateLimitManager()

        # Add a very restrictive service for testing
        config = RateLimitConfig(requests_per_second=1.0, burst_limit=1)
        manager.add_service("test_service", config)

        # First request should succeed immediately
        await manager.wait_and_acquire("test_service")

        # Second request should wait
        start_time = time.time()
        await manager.wait_and_acquire("test_service")
        elapsed = time.time() - start_time

        # Should have waited at least 0.5 seconds
        assert elapsed >= 0.5

    def test_service_statistics(self):
        """Test service statistics tracking."""
        manager = ServiceRateLimitManager()

        # Get stats for a service
        stats = manager.get_service_stats("arxiv")

        expected_keys = [
            "service",
            "rate_limit_status",
            "total_requests",
            "requests_last_minute",
            "last_request_time"
        ]

        for key in expected_keys:
            assert key in stats

        assert stats["service"] == "arxiv"
        assert stats["total_requests"] >= 0

    def test_all_service_statistics(self):
        """Test getting statistics for all services."""
        manager = ServiceRateLimitManager()

        all_stats = manager.get_all_stats()

        # Should have stats for all default services
        expected_services = ["arxiv", "hackernews", "rss", "gemini", "elevenlabs"]
        for service in expected_services:
            assert service in all_stats


class TestRateLimitedRequest:
    """Test the rate_limited_request utility function."""

    @pytest.mark.asyncio
    async def test_rate_limited_request_success(self):
        """Test successful rate limited request."""

        async def mock_request(value):
            """Mock async request function."""
            return f"result_{value}"

        result = await rate_limited_request(
            "test_service",
            mock_request,
            "test_value"
        )

        assert result == "result_test_value"

    @pytest.mark.asyncio
    async def test_rate_limited_request_with_kwargs(self):
        """Test rate limited request with keyword arguments."""

        async def mock_request(value, multiplier=1):
            """Mock async request function."""
            return value * multiplier

        result = await rate_limited_request(
            "test_service",
            mock_request,
            5,
            multiplier=3
        )

        assert result == 15

    @pytest.mark.asyncio
    async def test_rate_limited_request_error_handling(self):
        """Test error handling in rate limited requests."""

        async def failing_request():
            """Mock failing request function."""
            raise ValueError("Test error")

        with pytest.raises(ValueError, match="Test error"):
            await rate_limited_request(
                "test_service",
                failing_request
            )


class TestGlobalManager:
    """Test the global rate limit manager."""

    def test_get_rate_limit_manager_singleton(self):
        """Test that get_rate_limit_manager returns singleton."""
        manager1 = get_rate_limit_manager()
        manager2 = get_rate_limit_manager()

        assert manager1 is manager2
        assert isinstance(manager1, ServiceRateLimitManager)


@pytest.mark.asyncio
async def test_integration_rate_limiting():
    """Integration test for rate limiting functionality."""
    manager = get_rate_limit_manager()

    # Add a test service with known limits
    config = RateLimitConfig(requests_per_second=2.0, burst_limit=3)
    manager.add_service("integration_test", config)

    # Should be able to make burst requests
    results = []
    for i in range(3):
        acquired = await manager.acquire("integration_test")
        results.append(acquired)

    assert all(results)  # All should succeed

    # Next request should be rate limited
    assert await manager.acquire("integration_test") is False

    # Check statistics
    stats = manager.get_service_stats("integration_test")
    assert stats["total_requests"] == 3
    assert stats["rate_limit_status"]["available_tokens"] < 1
