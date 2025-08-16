"""
Middleware package for the AI news aggregator.

Provides production-ready middleware components for Vercel deployment.
"""

from .production import (
    TimeoutMiddleware,
    PerformanceMonitoringMiddleware,
    ErrorHandlingMiddleware,
    CORSSecurityMiddleware,
    setup_production_middleware
)

__all__ = [
    "TimeoutMiddleware",
    "PerformanceMonitoringMiddleware", 
    "ErrorHandlingMiddleware",
    "CORSSecurityMiddleware",
    "setup_production_middleware"
]