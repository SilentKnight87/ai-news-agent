"""
Production middleware for Vercel deployment.

This module provides middleware components optimized for serverless deployment,
including request timeouts, performance monitoring, and error handling.
"""

import asyncio
import time
import logging
import traceback
from datetime import datetime
from typing import Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class TimeoutMiddleware(BaseHTTPMiddleware):
    """
    Middleware to enforce request timeouts for Vercel Fluid Compute.
    
    Ensures requests complete within Vercel's 300s maxDuration limit,
    with a safety buffer to allow proper response handling.
    """

    def __init__(self, app, timeout_seconds: float = 290.0):
        """
        Initialize timeout middleware.
        
        Args:
            app: FastAPI application instance.
            timeout_seconds: Maximum request duration in seconds.
                           Default: 290s (10s buffer for 300s Vercel limit)
        """
        super().__init__(app)
        self.timeout_seconds = timeout_seconds
        logger.info(f"Timeout middleware initialized with {timeout_seconds}s limit")

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request with timeout enforcement.
        
        Args:
            request: Incoming HTTP request.
            call_next: Next middleware or route handler.
            
        Returns:
            Response: HTTP response or timeout error.
        """
        try:
            response = await asyncio.wait_for(
                call_next(request),
                timeout=self.timeout_seconds
            )
            return response
            
        except asyncio.TimeoutError:
            logger.error(
                f"Request timeout after {self.timeout_seconds}s",
                extra={
                    "path": request.url.path,
                    "method": request.method,
                    "timeout_seconds": self.timeout_seconds
                }
            )
            return JSONResponse(
                status_code=408,
                content={
                    "error": "Request timeout",
                    "message": f"Request exceeded {self.timeout_seconds}s limit",
                    "error_code": "REQUEST_TIMEOUT"
                }
            )


class PerformanceMonitoringMiddleware(BaseHTTPMiddleware):
    """
    Middleware to monitor request performance and log metrics.
    
    Provides structured logging for Vercel dashboard analysis and
    helps identify performance bottlenecks in production.
    """

    def __init__(self, app):
        """
        Initialize performance monitoring middleware.
        
        Args:
            app: FastAPI application instance.
        """
        super().__init__(app)
        logger.info("Performance monitoring middleware initialized")

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request with performance monitoring.
        
        Args:
            request: Incoming HTTP request.
            call_next: Next middleware or route handler.
            
        Returns:
            Response: HTTP response with performance headers.
        """
        start_time = time.time()
        start_memory = self._get_memory_usage()
        
        # Process request
        response = await call_next(request)
        
        # Calculate metrics
        duration = time.time() - start_time
        end_memory = self._get_memory_usage()
        memory_delta = end_memory - start_memory
        
        # Log structured performance data
        logger.info(
            "Request completed",
            extra={
                "path": request.url.path,
                "method": request.method,
                "status_code": response.status_code,
                "duration_seconds": round(duration, 3),
                "memory_start_mb": round(start_memory, 2),
                "memory_end_mb": round(end_memory, 2),
                "memory_delta_mb": round(memory_delta, 2),
                "timestamp": datetime.utcnow().isoformat(),
                "user_agent": request.headers.get("user-agent", "unknown"),
                "content_length": response.headers.get("content-length", 0)
            }
        )
        
        # Add performance headers for debugging
        response.headers["X-Response-Time"] = f"{duration:.3f}s"
        response.headers["X-Memory-Usage"] = f"{end_memory:.2f}MB"
        
        return response

    def _get_memory_usage(self) -> float:
        """
        Get current memory usage in MB.
        
        Returns:
            float: Memory usage in megabytes.
        """
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024
        except ImportError:
            # Fallback if psutil not available
            import sys
            return sys.getsizeof(sys.modules) / 1024 / 1024


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to handle and log application errors consistently.
    
    Provides structured error responses and detailed logging for
    debugging in production environments.
    """

    def __init__(self, app):
        """
        Initialize error handling middleware.
        
        Args:
            app: FastAPI application instance.
        """
        super().__init__(app)
        logger.info("Error handling middleware initialized")

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request with error handling.
        
        Args:
            request: Incoming HTTP request.
            call_next: Next middleware or route handler.
            
        Returns:
            Response: HTTP response or error response.
        """
        try:
            response = await call_next(request)
            return response
            
        except Exception as exc:
            # Log detailed error information
            error_id = f"err_{int(time.time())}"
            
            logger.error(
                f"Unhandled exception: {error_id}",
                extra={
                    "error_id": error_id,
                    "path": request.url.path,
                    "method": request.method,
                    "exception_type": type(exc).__name__,
                    "exception_message": str(exc),
                    "traceback": traceback.format_exc(),
                    "timestamp": datetime.utcnow().isoformat(),
                    "user_agent": request.headers.get("user-agent", "unknown")
                }
            )
            
            # Return structured error response
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal server error",
                    "message": "An unexpected error occurred",
                    "error_code": "INTERNAL_ERROR",
                    "error_id": error_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )


class CORSSecurityMiddleware(BaseHTTPMiddleware):
    """
    Enhanced CORS middleware for production security.
    
    Provides additional security headers and more granular CORS control
    for production deployment.
    """

    def __init__(self, app, allowed_origins: list[str] = None):
        """
        Initialize CORS security middleware.
        
        Args:
            app: FastAPI application instance.
            allowed_origins: List of allowed origin domains.
        """
        super().__init__(app)
        self.allowed_origins = allowed_origins or []
        logger.info(f"CORS security middleware initialized with origins: {self.allowed_origins}")

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request with enhanced CORS and security headers.
        
        Args:
            request: Incoming HTTP request.
            call_next: Next middleware or route handler.
            
        Returns:
            Response: HTTP response with security headers.
        """
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        # Enhanced CORS validation with wildcard support
        origin = request.headers.get("origin")
        if origin and self.allowed_origins:
            origin_allowed = False
            
            # Check direct match first
            if origin in self.allowed_origins:
                origin_allowed = True
            else:
                # Check wildcard patterns (e.g., https://*.vercel.app)
                for allowed_origin in self.allowed_origins:
                    if "*" in allowed_origin:
                        # Convert wildcard pattern to regex
                        pattern = allowed_origin.replace("*", ".*")
                        import re
                        if re.match(f"^{pattern}$", origin):
                            origin_allowed = True
                            break
            
            if origin_allowed:
                response.headers["Access-Control-Allow-Origin"] = origin
                response.headers["Access-Control-Allow-Credentials"] = "true"
                response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
                response.headers["Access-Control-Allow-Headers"] = "*"
                response.headers["Vary"] = "Origin"
            else:
                logger.warning(
                    f"CORS origin not allowed: {origin}",
                    extra={
                        "origin": origin,
                        "allowed_origins": self.allowed_origins,
                        "path": request.url.path
                    }
                )
        
        return response


def setup_production_middleware(app, settings):
    """
    Setup all production middleware for the FastAPI application.
    
    Args:
        app: FastAPI application instance.
        settings: Application settings with configuration.
    """
    # Parse allowed origins from settings
    allowed_origins = []
    if settings.cors_allowed_origins:
        allowed_origins = [
            origin.strip() 
            for origin in settings.cors_allowed_origins.split(",")
            if origin.strip()
        ]
    
    # Add middleware in reverse order (last added = first executed)
    app.add_middleware(CORSSecurityMiddleware, allowed_origins=allowed_origins)
    app.add_middleware(ErrorHandlingMiddleware)
    app.add_middleware(PerformanceMonitoringMiddleware)
    app.add_middleware(TimeoutMiddleware, timeout_seconds=290.0)
    
    logger.info("All production middleware configured successfully")