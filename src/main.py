"""
Main FastAPI application for the AI news aggregator.

This module sets up the FastAPI application with all routes, middleware,
and startup/shutdown event handlers.
"""

import logging
import os
import sys
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .api.routes import router
from .config import get_settings

# Configure logging
handlers = [logging.StreamHandler(sys.stdout)]

# Add file handler if logs directory exists
if os.path.exists("logs"):
    handlers.append(logging.FileHandler("logs/app.log", mode="a"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=handlers
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan handler for startup and shutdown events.

    Args:
        app: FastAPI application instance.
    """
    # Startup
    logger.info("Starting AI News Aggregator API")

    settings = get_settings()
    logger.info(f"Configuration loaded - Debug mode: {settings.debug}")

    # Test database connection
    try:
        from .api.dependencies import get_supabase_client
        supabase = get_supabase_client()

        # Simple health check
        supabase.table("articles").select("id").limit(1).execute()
        logger.info("Database connection verified")

    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        logger.warning("Application starting without database connection")

    # Initialize AI services
    try:
        logger.info("News analyzer initialized")

        from .services.embeddings import get_embeddings_service
        embeddings_service = get_embeddings_service()
        logger.info(f"Embeddings service initialized with model: {embeddings_service.model_name}")

    except Exception as e:
        logger.error(f"Failed to initialize AI services: {e}")

    logger.info("Application startup complete")

    yield

    # Shutdown
    logger.info("Shutting down AI News Aggregator API")


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.

    Returns:
        FastAPI: Configured application instance.
    """
    settings = get_settings()

    # Create FastAPI app
    app = FastAPI(
        title="AI News Aggregator",
        description="AI-powered news aggregator with PydanticAI and Supabase",
        version="0.1.0",
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
        lifespan=lifespan
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include API routes
    app.include_router(router, prefix="/api/v1")

    # Root endpoint
    @app.get("/")
    async def root():
        """Root endpoint with basic information."""
        return {
            "name": "AI News Aggregator",
            "version": "0.1.0",
            "status": "running",
            "docs_url": "/docs" if settings.debug else "disabled"
        }

    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request, exc: Exception):
        """Handle unexpected exceptions."""
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
                "error_code": "INTERNAL_ERROR"
            }
        )

    return app


# Create the application instance
app = create_app()


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()

    # Ensure logs directory exists
    import os
    os.makedirs("logs", exist_ok=True)

    logger.info("Starting development server")

    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
