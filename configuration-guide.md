# Configuration Guide

The AI News Aggregator uses JSON configuration files to manage data sources dynamically. This allows you to add, remove, or modify sources without changing code or redeploying the application.

## Configuration Files

All configuration files are located in the `/config` directory:

### 1. GitHub Repositories (`config/github_repos.json`)

Lists GitHub repositories to track for new releases:

```json
[
  "anthropics/anthropic-sdk-python",
  "openai/openai-python",
  "langchain-ai/langchain",
  "ollama/ollama"
]
```

Add or remove repositories by editing this array. Format: `"owner/repository"`

### 2. Reddit Subreddits (`config/reddit_subs.json`)

Lists subreddits to monitor for AI/ML discussions:

```json
[
  "LocalLLaMA",
  "MachineLearning",
  "artificial",
  "singularity",
  "OpenAI"
]
```

Add or remove subreddit names (without the "r/" prefix).

### 3. ArXiv Categories (`config/arxiv_categories.json`)

Configures ArXiv paper categories and fetch limits:

```json
{
  "categories": [
    "cs.AI",
    "cs.LG",
    "cs.CL",
    "cs.CV",
    "cs.NE",
    "stat.ML"
  ],
  "max_results": 50
}
```

- `categories`: ArXiv category codes to search
- `max_results`: Default number of papers to fetch per run

## Hot Reload

The configuration files are loaded when each fetcher is initialized. To apply configuration changes:

1. **For scheduled tasks**: Changes will be applied on the next scheduled run (no restart needed)
2. **For manual runs**: Restart the application or wait for the next scheduled execution

## Adding New Sources

To add new sources to any fetcher:

1. Edit the appropriate JSON file
2. Add your source to the array
3. Save the file
4. Changes will be applied on next fetcher initialization

## Validation

- GitHub: Repositories must exist and be publicly accessible
- Reddit: Subreddits must exist and be accessible
- ArXiv: Use valid ArXiv category codes (see https://arxiv.org/category_taxonomy)

## Fallback Behavior

If a configuration file is missing or invalid:
- The fetcher will log a warning
- Default sources will be used
- The application will continue to function

This ensures resilience even if configuration files are accidentally deleted or corrupted.