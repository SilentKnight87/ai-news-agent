"""
Configuration management for the AI news aggregator.

Uses Pydantic Settings for environment variable validation and type safety.
"""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    Uses pydantic-settings for automatic validation and type conversion.
    """

    # Supabase configuration
    supabase_url: str = Field(..., description="Supabase project URL")
    supabase_anon_key: str | None = Field(None, description="Supabase anonymous key (optional if service role key available)")
    supabase_service_role_key: str | None = Field(None, description="Supabase service role key for write operations")

    # AI Service API keys
    gemini_api_key: str = Field(..., description="Google Gemini API key")
    elevenlabs_api_key: str | None = Field(None, description="ElevenLabs API key for TTS")
    hf_api_key: str | None = Field(None, description="HuggingFace API key")
    openai_api_key: str | None = Field(None, description="OpenAI API key for embeddings")

    # Reddit API credentials
    reddit_client_id: str | None = Field(None, description="Reddit OAuth client ID")
    reddit_client_secret: str | None = Field(None, description="Reddit OAuth client secret")
    reddit_user_agent: str = Field("AI-News-Aggregator/1.0", description="Reddit API user agent")
    reddit_username: str | None = Field(None, description="Reddit username for user agent")

    # GitHub API credentials
    github_token: str | None = Field(None, description="GitHub personal access token")
    
    # GitHub OAuth credentials
    github_oauth_client_id: str | None = Field(None, description="GitHub OAuth client ID")
    github_client_secret: str | None = Field(None, description="GitHub OAuth client secret")
    
    # OpenRouter API key
    openrouter_api_key: str | None = Field(None, description="OpenRouter API key for LLM access")

    # Application configuration
    fetch_interval_minutes: int = Field(30, description="Minutes between fetching cycles")
    digest_hour_utc: int = Field(17, ge=0, le=23, description="Hour (UTC) to generate daily digest")

    # Rate limiting
    arxiv_delay_seconds: float = Field(3.0, description="Delay between ArXiv requests")
    hackernews_requests_per_second: float = Field(1.0, description="HackerNews requests per second")

    # Vector similarity
    similarity_threshold: float = Field(0.85, ge=0.0, le=1.0, description="Cosine similarity threshold for duplicates")

    # Content limits
    max_digest_chars: int = Field(2000, description="Maximum characters in daily digest for TTS")
    max_articles_per_fetch: int = Field(100, description="Maximum articles to fetch per source")

    # Embedding configuration
    embedding_model: str = Field("sentence-transformers/all-MiniLM-L6-v2", description="HuggingFace embedding model")
    embedding_batch_size: int = Field(100, description="Batch size for embedding generation")
    embeddings_provider: str = Field("local", description="Embeddings provider: local, openai, huggingface")

    # CORS configuration
    cors_allowed_origins: str = Field(
        "http://localhost:3000",
        description="Comma-separated list of allowed CORS origins"
    )

    # Development settings
    debug: bool = Field(False, description="Enable debug mode")
    log_level: str = Field("INFO", description="Logging level")

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }


@lru_cache
def get_settings() -> Settings:
    """
    Get application settings with caching.

    Using @lru_cache ensures we only create one instance of Settings
    throughout the application lifetime, which is important for performance
    and consistency.

    Returns:
        Settings: Validated application settings.
    """
    return Settings()
