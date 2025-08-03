"""
Rate limiting service for API calls and external requests.

This module provides configurable rate limiting for different services
to respect API limits and avoid being blocked by external services.
"""

import asyncio
import logging
import time
from collections import defaultdict, deque
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""

    requests_per_second: float
    burst_limit: int = 10
    cooldown_seconds: float = 60.0


class RateLimiter:
    """
    Token bucket rate limiter with burst support.
    
    Implements a token bucket algorithm that allows bursts up to a limit
    while maintaining an average rate over time.
    """

    def __init__(self, config: RateLimitConfig):
        """
        Initialize rate limiter.
        
        Args:
            config: Rate limiting configuration.
        """
        self.config = config
        self.tokens = float(config.burst_limit)
        self.last_update = time.time()
        self.lock = asyncio.Lock()

        logger.debug(
            f"Rate limiter initialized: {config.requests_per_second} req/s, "
            f"burst: {config.burst_limit}"
        )

    async def acquire(self, tokens: int = 1) -> bool:
        """
        Acquire tokens from the bucket.
        
        Args:
            tokens: Number of tokens to acquire.
            
        Returns:
            bool: True if tokens were acquired, False if rate limited.
        """
        async with self.lock:
            now = time.time()

            # Add tokens based on elapsed time
            elapsed = now - self.last_update
            tokens_to_add = elapsed * self.config.requests_per_second
            self.tokens = min(
                self.config.burst_limit,
                self.tokens + tokens_to_add
            )
            self.last_update = now

            # Check if we have enough tokens
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True

            return False

    async def wait_for_tokens(self, tokens: int = 1) -> None:
        """
        Wait until tokens are available and acquire them.
        
        Args:
            tokens: Number of tokens to acquire.
        """
        while not await self.acquire(tokens):
            # Calculate wait time based on token deficit
            async with self.lock:
                deficit = tokens - self.tokens
                wait_time = deficit / self.config.requests_per_second
                wait_time = min(wait_time, self.config.cooldown_seconds)

            logger.debug(f"Rate limited, waiting {wait_time:.2f}s")
            await asyncio.sleep(wait_time)

    def get_status(self) -> dict[str, float]:
        """
        Get current rate limiter status.
        
        Returns:
            Dict: Current tokens and configuration.
        """
        return {
            "available_tokens": self.tokens,
            "max_tokens": self.config.burst_limit,
            "requests_per_second": self.config.requests_per_second,
            "utilization": 1.0 - (self.tokens / self.config.burst_limit)
        }


class ServiceRateLimitManager:
    """
    Manages rate limiters for different external services.
    
    Provides service-specific rate limiting with different configurations
    for various APIs and external services.
    """

    def __init__(self):
        """Initialize the rate limit manager."""
        self.limiters: dict[str, RateLimiter] = {}
        self.request_history: dict[str, deque] = defaultdict(
            lambda: deque(maxlen=1000)
        )

        # Initialize default service configurations
        self._initialize_service_limiters()

        logger.info("Service rate limit manager initialized")

    def _initialize_service_limiters(self) -> None:
        """Initialize rate limiters for known services."""

        # ArXiv API - conservative rate limiting
        self.limiters["arxiv"] = RateLimiter(RateLimitConfig(
            requests_per_second=0.33,  # ~1 request per 3 seconds
            burst_limit=3,
            cooldown_seconds=10.0
        ))

        # HackerNews API - more permissive
        self.limiters["hackernews"] = RateLimiter(RateLimitConfig(
            requests_per_second=1.0,  # 1 request per second
            burst_limit=10,
            cooldown_seconds=5.0
        ))

        # Generic RSS feeds - moderate limiting
        self.limiters["rss"] = RateLimiter(RateLimitConfig(
            requests_per_second=0.5,  # 1 request per 2 seconds
            burst_limit=5,
            cooldown_seconds=10.0
        ))

        # Google Gemini API - respect their limits
        self.limiters["gemini"] = RateLimiter(RateLimitConfig(
            requests_per_second=2.0,  # 2 requests per second
            burst_limit=20,
            cooldown_seconds=30.0
        ))

        # ElevenLabs TTS API
        self.limiters["elevenlabs"] = RateLimiter(RateLimitConfig(
            requests_per_second=0.1,  # 1 request per 10 seconds (conservative)
            burst_limit=2,
            cooldown_seconds=60.0
        ))

        logger.debug(f"Initialized rate limiters for {len(self.limiters)} services")

    async def acquire(self, service: str, tokens: int = 1) -> bool:
        """
        Try to acquire tokens for a service.
        
        Args:
            service: Service identifier.
            tokens: Number of tokens to acquire.
            
        Returns:
            bool: True if tokens were acquired.
        """
        limiter = self._get_limiter(service)
        acquired = await limiter.acquire(tokens)

        # Track request for statistics
        if acquired:
            self.request_history[service].append(time.time())

        return acquired

    async def wait_and_acquire(self, service: str, tokens: int = 1) -> None:
        """
        Wait for tokens to be available and acquire them.
        
        Args:
            service: Service identifier.
            tokens: Number of tokens to acquire.
        """
        limiter = self._get_limiter(service)
        await limiter.wait_for_tokens(tokens)

        # Track request for statistics
        self.request_history[service].append(time.time())

        logger.debug(f"Acquired {tokens} tokens for {service}")

    def add_service(
        self,
        service: str,
        config: RateLimitConfig
    ) -> None:
        """
        Add a custom rate limiter for a service.
        
        Args:
            service: Service identifier.
            config: Rate limiting configuration.
        """
        self.limiters[service] = RateLimiter(config)
        logger.info(f"Added rate limiter for service: {service}")

    def _get_limiter(self, service: str) -> RateLimiter:
        """
        Get rate limiter for a service, creating default if needed.
        
        Args:
            service: Service identifier.
            
        Returns:
            RateLimiter: Rate limiter instance.
        """
        if service not in self.limiters:
            # Create default rate limiter for unknown services
            logger.warning(f"Creating default rate limiter for unknown service: {service}")
            self.limiters[service] = RateLimiter(RateLimitConfig(
                requests_per_second=1.0,
                burst_limit=5,
                cooldown_seconds=10.0
            ))

        return self.limiters[service]

    def get_service_stats(self, service: str) -> dict[str, any]:
        """
        Get statistics for a service.
        
        Args:
            service: Service identifier.
            
        Returns:
            Dict: Service statistics including rate limit status.
        """
        limiter = self._get_limiter(service)
        history = self.request_history[service]

        # Calculate request rate over last minute
        now = time.time()
        recent_requests = [
            t for t in history
            if now - t <= 60.0
        ]

        return {
            "service": service,
            "rate_limit_status": limiter.get_status(),
            "total_requests": len(history),
            "requests_last_minute": len(recent_requests),
            "last_request_time": history[-1] if history else None
        }

    def get_all_stats(self) -> dict[str, dict[str, any]]:
        """
        Get statistics for all services.
        
        Returns:
            Dict: Statistics for all tracked services.
        """
        return {
            service: self.get_service_stats(service)
            for service in self.limiters.keys()
        }


# Global rate limit manager instance
_rate_limit_manager: ServiceRateLimitManager | None = None


def get_rate_limit_manager() -> ServiceRateLimitManager:
    """
    Get the global rate limit manager instance.
    
    Returns:
        ServiceRateLimitManager: Global rate limit manager.
    """
    global _rate_limit_manager
    if _rate_limit_manager is None:
        _rate_limit_manager = ServiceRateLimitManager()
    return _rate_limit_manager


async def rate_limited_request(
    service: str,
    request_func,
    *args,
    tokens: int = 1,
    **kwargs
):
    """
    Execute a request with rate limiting.
    
    Args:
        service: Service identifier for rate limiting.
        request_func: Async function to execute.
        tokens: Number of tokens to acquire.
        *args: Arguments for request_func.
        **kwargs: Keyword arguments for request_func.
        
    Returns:
        Result from request_func.
    """
    manager = get_rate_limit_manager()
    await manager.wait_and_acquire(service, tokens)

    try:
        result = await request_func(*args, **kwargs)
        return result
    except Exception as e:
        logger.error(f"Rate limited request failed for {service}: {e}")
        raise
