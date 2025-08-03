"""
Hugging Face Models fetcher for tracking trending and new model releases.

This module implements fetching from Hugging Face Models API with filtering
for AI/ML models and metadata extraction.
"""

import asyncio
import logging
from datetime import UTC, datetime
from typing import Any

from ..models.articles import Article, ArticleSource
from .base import BaseFetcher, FetchError, RateLimitedHTTPClient

logger = logging.getLogger(__name__)


class HuggingFaceFetcher(BaseFetcher):
    """
    Fetcher for Hugging Face Models API.
    
    Tracks trending and new model releases with filtering for
    text-generation and related AI/ML models.
    """

    def __init__(self, hf_api_key: str | None = None):
        """
        Initialize Hugging Face fetcher.
        
        Args:
            hf_api_key: Optional Hugging Face API key for higher rate limits.
        """
        # 1000 requests per hour = ~0.36 second delay, use 0.1 for safety margin
        super().__init__(source=ArticleSource.HUGGINGFACE, rate_limit_delay=0.1)

        self.base_url = "https://huggingface.co/api"
        self.client = RateLimitedHTTPClient(requests_per_second=2.5)

        # Set up headers with optional API key
        self.headers = {
            "User-Agent": "AI-News-Aggregator/1.0"
        }
        if hf_api_key:
            self.headers["Authorization"] = f"Bearer {hf_api_key}"

        logger.info("Hugging Face fetcher initialized")

    async def fetch(self, max_articles: int = 50) -> list[Article]:
        """
        Fetch trending and new models from Hugging Face.
        
        Args:
            max_articles: Maximum number of articles to return.
            
        Returns:
            List[Article]: List of model articles.
            
        Raises:
            FetchError: If fetching fails.
        """
        try:
            logger.info("Fetching models from Hugging Face API")

            # Fetch both trending and new models concurrently
            trending_task = self._fetch_trending_models()
            new_models_task = self._fetch_new_models()

            trending_models, new_models = await asyncio.gather(
                trending_task, new_models_task, return_exceptions=True
            )

            # Handle exceptions
            if isinstance(trending_models, Exception):
                logger.warning(f"Failed to fetch trending models: {trending_models}")
                trending_models = []
            if isinstance(new_models, Exception):
                logger.warning(f"Failed to fetch new models: {new_models}")
                new_models = []

            # Combine and deduplicate models
            all_models = []
            seen_ids = set()

            # Add trending models first (higher priority)
            for model in trending_models:
                if model['id'] not in seen_ids:
                    all_models.append(model)
                    seen_ids.add(model['id'])

            # Add new models
            for model in new_models:
                if model['id'] not in seen_ids:
                    all_models.append(model)
                    seen_ids.add(model['id'])

            # Filter for relevant AI/ML models and convert to articles
            articles = []
            for model in all_models:
                if self._is_relevant_model(model):
                    try:
                        article = self._model_to_article(model)
                        if article:
                            articles.append(article)
                    except Exception as e:
                        logger.warning(f"Failed to convert model {model.get('id', 'unknown')}: {e}")
                        continue

            # Sort by downloads/likes and limit results
            articles.sort(key=lambda x: x.metadata.get('downloads', 0), reverse=True)
            limited_articles = articles[:max_articles]

            logger.info(f"Successfully fetched {len(limited_articles)} model articles from Hugging Face")
            return limited_articles

        except Exception as e:
            error_msg = f"Failed to fetch from Hugging Face API: {str(e)}"
            logger.error(error_msg)
            raise FetchError(error_msg, source=self.source)

    async def _fetch_trending_models(self) -> list[dict[str, Any]]:
        """
        Fetch trending models from Hugging Face API.
        
        Returns:
            List[dict]: List of trending model data.
        """
        url = f"{self.base_url}/models"
        params = {
            "sort": "trending",
            "limit": 25,
            "full": "true"  # Get complete model information
        }

        response = await self.client.get(url, params=params, headers=self.headers)
        return response.json()

    async def _fetch_new_models(self) -> list[dict[str, Any]]:
        """
        Fetch recently updated models from Hugging Face API.
        
        Returns:
            List[dict]: List of new model data.
        """
        url = f"{self.base_url}/models"
        params = {
            "sort": "lastModified",
            "limit": 25,
            "full": "true"  # Get complete model information
        }

        response = await self.client.get(url, params=params, headers=self.headers)
        return response.json()

    def _is_relevant_model(self, model: dict[str, Any]) -> bool:
        """
        Check if a model is relevant for AI news aggregation.
        
        Args:
            model: Model data from HF API.
            
        Returns:
            bool: True if model is relevant.
        """
        # Get model tags
        tags = model.get('tags', [])

        # Relevant model types for AI news
        relevant_tags = {
            'text-generation',
            'text2text-generation',
            'conversational',
            'question-answering',
            'summarization',
            'translation',
            'text-classification',
            'token-classification',
            'feature-extraction',
            'sentence-similarity',
            'fill-mask',
            'image-classification',
            'object-detection',
            'image-to-text',
            'text-to-image',
            'automatic-speech-recognition',
            'text-to-speech',
            'audio-classification'
        }

        # Check if model has relevant tags
        has_relevant_tag = any(tag in relevant_tags for tag in tags)

        # Also include models with high download counts (likely important)
        high_downloads = model.get('downloads', 0) > 1000

        # Exclude models that are clearly datasets or spaces
        model_id = model.get('id', '')
        is_dataset = 'dataset' in tags or '/datasets/' in model_id
        is_space = 'space' in tags or '/spaces/' in model_id

        return (has_relevant_tag or high_downloads) and not (is_dataset or is_space)

    def _model_to_article(self, model: dict[str, Any]) -> Article | None:
        """
        Convert HF model data to Article object.
        
        Args:
            model: Model data from HF API.
            
        Returns:
            Article: Converted article or None if conversion fails.
        """
        try:
            model_id = model.get('id')
            if not model_id:
                return None

            # Create title
            title = f"🤗 {model_id}"

            # Create content from model card or description
            content = ""
            if model.get('cardData', {}).get('base_model'):
                content += f"Based on: {model['cardData']['base_model']}. "

            # Add model description
            if model.get('description'):
                content += model['description']
            else:
                # Generate basic description from tags
                tags = model.get('tags', [])
                if tags:
                    content += f"AI model for {', '.join(tags[:3])}."
                else:
                    content += "New AI model on Hugging Face."

            # Create URL
            url = f"https://huggingface.co/{model_id}"

            # Extract author
            author = model_id.split('/')[0] if '/' in model_id else "Hugging Face"

            # Parse published date
            published_at = self._parse_model_date(model)

            # Extract metadata
            metadata = self._extract_model_metadata(model)

            return Article(
                source_id=model_id,
                source=ArticleSource.HUGGINGFACE,
                title=title,
                content=content,
                url=url,
                author=author,
                published_at=published_at,
                fetched_at=datetime.now(UTC),
                metadata=metadata,
                summary=None,
                relevance_score=None,
                embedding=None,
                is_duplicate=False,
                duplicate_of=None
            )

        except Exception as e:
            logger.warning(f"Failed to convert model {model.get('id', 'unknown')}: {e}")
            return None

    def _parse_model_date(self, model: dict[str, Any]) -> datetime:
        """
        Parse model creation/update date.
        
        Args:
            model: Model data from HF API.
            
        Returns:
            datetime: Parsed date or current time if parsing fails.
        """
        # Try different date fields
        for field in ['lastModified', 'createdAt', 'updatedAt']:
            date_str = model.get(field)
            if date_str:
                try:
                    # Parse ISO format datetime
                    if date_str.endswith('Z'):
                        date_str = date_str[:-1] + '+00:00'
                    return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                except (ValueError, TypeError) as e:
                    logger.debug(f"Failed to parse date '{date_str}' from field '{field}': {e}")
                    continue

        # Fallback to current time
        return datetime.now(UTC)

    def _extract_model_metadata(self, model: dict[str, Any]) -> dict[str, Any]:
        """
        Extract Hugging Face specific metadata.
        
        Args:
            model: Model data from HF API.
            
        Returns:
            dict: Extracted metadata.
        """
        metadata = {
            "platform": "huggingface",
            "model_id": model.get('id'),
            "downloads": model.get('downloads', 0),
            "likes": model.get('likes', 0),
            "tags": model.get('tags', [])
        }

        # Add model size information if available
        if 'safetensors' in model.get('tags', []):
            metadata["format"] = "safetensors"
        elif 'pytorch' in model.get('tags', []):
            metadata["format"] = "pytorch"

        # Add license information
        card_data = model.get('cardData', {})
        if card_data.get('license'):
            metadata["license"] = card_data['license']

        # Add base model information
        if card_data.get('base_model'):
            metadata["base_model"] = card_data['base_model']

        # Add pipeline tag (primary task)
        if model.get('pipeline_tag'):
            metadata["pipeline_tag"] = model['pipeline_tag']

        # Check if trending (simple heuristic based on recent activity)
        recent_downloads = metadata["downloads"]
        recent_likes = metadata["likes"]
        if recent_downloads > 10000 or recent_likes > 100:
            metadata["trending"] = True

        return metadata
