"""
GitHub releases fetcher for AI development tools and frameworks.

This module implements fetching from GitHub Releases API with filtering
for recent releases from important AI/ML repositories.
"""

import asyncio
import json
import logging
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from ..models.articles import Article, ArticleSource
from .base import BaseFetcher, FetchError, RateLimitedHTTPClient

logger = logging.getLogger(__name__)


class GitHubFetcher(BaseFetcher):
    """
    Fetcher for GitHub releases from AI/ML repositories.
    
    Tracks new releases and updates from important AI development
    tools and frameworks.
    """

    def __init__(self, github_token: str | None = None):
        """
        Initialize GitHub fetcher.
        
        Args:
            github_token: Optional GitHub personal access token for higher rate limits.
        """
        # 5000 requests per hour authenticated = ~0.72 second delay, use 0.5 for safety
        # 60 requests per hour unauthenticated = 60 second delay
        rate_delay = 0.5 if github_token else 60.0
        super().__init__(source=ArticleSource.GITHUB, rate_limit_delay=rate_delay)

        self.base_url = "https://api.github.com"
        self.client = RateLimitedHTTPClient(requests_per_second=2.0 if github_token else 0.017)

        # Set up headers with optional token
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "AI-News-Aggregator/1.0"
        }
        if github_token:
            self.headers["Authorization"] = f"token {github_token}"

        # Load repositories from config file
        self.repositories = self._load_repositories()
        logger.info(f"GitHub fetcher initialized tracking {len(self.repositories)} repositories")

    def _load_repositories(self) -> list[str]:
        """Load GitHub repositories from config file."""
        config_path = Path(__file__).parent.parent.parent / "config" / "github_repos.json"

        try:
            with open(config_path) as f:
                repos = json.load(f)
                logger.debug(f"Loaded {len(repos)} repositories from config")
                return repos
        except FileNotFoundError:
            logger.warning(f"Config file not found at {config_path}, using defaults")
            # Fallback to default repositories
            return [
                "anthropics/anthropic-sdk-python",
                "openai/openai-python",
                "langchain-ai/langchain",
                "ollama/ollama"
            ]
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in config file: {e}")
            return []

    async def fetch(self, max_articles: int = 50) -> list[Article]:
        """
        Fetch recent releases from tracked repositories.
        
        Args:
            max_articles: Maximum number of articles to return.
            
        Returns:
            List[Article]: List of release articles.
            
        Raises:
            FetchError: If fetching fails.
        """
        try:
            logger.info(f"Fetching releases from {len(self.repositories)} GitHub repositories")

            # Fetch releases from all repositories concurrently (with rate limiting)
            all_releases: list[dict[str, Any]] = []

            # Process repositories in batches to avoid overwhelming the API
            batch_size = 5
            for i in range(0, len(self.repositories), batch_size):
                batch = self.repositories[i:i + batch_size]

                # Create tasks for this batch
                tasks = [self._fetch_repo_releases(repo) for repo in batch]

                # Execute batch with error handling
                results = await asyncio.gather(*tasks, return_exceptions=True)

                for j, result in enumerate(results):
                    repo = batch[j]
                    if isinstance(result, Exception):
                        logger.warning(f"Failed to fetch releases from {repo}: {result}")
                    else:
                        all_releases.extend(result)

                # Small delay between batches
                if i + batch_size < len(self.repositories):
                    await asyncio.sleep(1.0)

            # Filter for recent releases (last 30 days)
            cutoff_date = datetime.now(UTC) - timedelta(days=30)
            recent_releases = [
                release for release in all_releases
                if self._parse_github_date(release).replace(tzinfo=UTC) >= cutoff_date
            ]

            # Convert to articles
            articles = []
            for release in recent_releases:
                try:
                    article = self._release_to_article(release)
                    if article:
                        articles.append(article)
                except Exception as e:
                    repo = release.get('html_url', 'unknown').split('/releases/')[0]
                    logger.warning(f"Failed to convert release from {repo}: {e}")
                    continue

            # Sort by published date (newest first) and limit results
            articles.sort(key=lambda x: x.published_at, reverse=True)
            limited_articles = articles[:max_articles]

            logger.info(f"Successfully fetched {len(limited_articles)} release articles from GitHub")
            return limited_articles

        except Exception as e:
            error_msg = f"Failed to fetch from GitHub API: {str(e)}"
            logger.error(error_msg)
            raise FetchError(error_msg, source=self.source)

    async def _fetch_repo_releases(self, repo: str) -> list[dict[str, Any]]:
        """
        Fetch releases from a specific repository.
        
        Args:
            repo: Repository in format "owner/name".
            
        Returns:
            List[dict]: List of release data.
        """
        try:
            url = f"{self.base_url}/repos/{repo}/releases"
            params = {
                "per_page": 10,  # Get last 10 releases
                "page": 1
            }

            # Apply rate limiting
            await self._apply_rate_limit()

            response = await self.client.get(url, params=params, headers=self.headers)
            releases = response.json()

            # Add repository info to each release
            for release in releases:
                release['repository'] = repo

            logger.debug(f"Fetched {len(releases)} releases from {repo}")
            return releases

        except Exception as e:
            logger.warning(f"Failed to fetch releases from {repo}: {e}")
            return []

    def _release_to_article(self, release: dict[str, Any]) -> Article | None:
        """
        Convert GitHub release to Article object.
        
        Args:
            release: Release data from GitHub API.
            
        Returns:
            Article: Converted article or None if conversion fails.
        """
        try:
            # Extract basic info
            repo = release.get('repository', 'unknown/unknown')
            tag_name = release.get('tag_name', 'v0.0.0')
            release_name = release.get('name') or tag_name

            # Create title
            repo_name = repo.split('/')[-1]
            title = f"🚀 {repo_name} {tag_name}"
            if release_name != tag_name:
                title += f" - {release_name}"

            # Create content from release notes
            content = ""
            body = release.get('body', '')
            if body:
                # Truncate long release notes
                if len(body) > 800:
                    content = body[:800] + "..."
                else:
                    content = body
            else:
                content = f"New release {tag_name} of {repo_name}."

            # Create URL
            url = release.get('html_url', f"https://github.com/{repo}/releases/tag/{tag_name}")

            # Extract author
            author_info = release.get('author', {})
            author = author_info.get('login', repo.split('/')[0])

            # Parse published date
            published_at = self._parse_github_date(release)

            # Extract metadata
            metadata = self._extract_release_metadata(release)

            return Article(
                source_id=f"github_{repo.replace('/', '_')}_{release.get('id', 'unknown')}",
                source=ArticleSource.GITHUB,
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
            logger.warning(f"Failed to convert release: {e}")
            return None

    def _parse_github_date(self, release: dict[str, Any]) -> datetime:
        """
        Parse GitHub release date.
        
        Args:
            release: Release data from GitHub API.
            
        Returns:
            datetime: Parsed date or current time if parsing fails.
        """
        # Try different date fields
        for field in ['published_at', 'created_at']:
            date_str = release.get(field)
            if date_str:
                try:
                    # Parse ISO format datetime
                    return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                except (ValueError, TypeError) as e:
                    logger.debug(f"Failed to parse date '{date_str}' from field '{field}': {e}")
                    continue

        # Fallback to current time
        return datetime.now(UTC)

    def _extract_release_metadata(self, release: dict[str, Any]) -> dict[str, Any]:
        """
        Extract GitHub release specific metadata.
        
        Args:
            release: Release data from GitHub API.
            
        Returns:
            dict: Extracted metadata.
        """
        metadata = {
            "platform": "github",
            "repository": release.get('repository', ''),
            "version": release.get('tag_name', ''),
            "release_id": release.get('id'),
            "is_prerelease": release.get('prerelease', False),
            "is_draft": release.get('draft', False)
        }

        # Add release name if different from tag
        release_name = release.get('name')
        if release_name and release_name != metadata["version"]:
            metadata["release_name"] = release_name

        # Count assets (downloads)
        assets = release.get('assets', [])
        if assets:
            metadata["asset_count"] = len(assets)
            total_downloads = sum(asset.get('download_count', 0) for asset in assets)
            metadata["total_downloads"] = total_downloads

        # Add tarball and zipball URLs
        if release.get('tarball_url'):
            metadata["tarball_url"] = release['tarball_url']
        if release.get('zipball_url'):
            metadata["zipball_url"] = release['zipball_url']

        # Check for breaking changes indicators in release notes
        body = release.get('body', '').lower()
        breaking_indicators = [
            'breaking change', 'breaking changes', 'breaking:',
            'breaking change:', '**breaking**', '[breaking]',
            'api change', 'major version', 'incompatible'
        ]

        has_breaking_changes = any(indicator in body for indicator in breaking_indicators)
        if has_breaking_changes:
            metadata["breaking_changes"] = True

        # Extract version type
        version = metadata["version"].lower()
        if 'alpha' in version:
            metadata["version_type"] = "alpha"
        elif 'beta' in version:
            metadata["version_type"] = "beta"
        elif 'rc' in version:
            metadata["version_type"] = "release_candidate"
        elif metadata["is_prerelease"]:
            metadata["version_type"] = "prerelease"
        else:
            metadata["version_type"] = "stable"

        return metadata
