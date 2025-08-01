## FEATURE:

- Engagement metrics tracking across all content sources (views, upvotes, downloads, stars)
- Trending detection algorithms based on engagement velocity and cross-source coverage
- Story clustering for major news that appears across multiple sources
- Real-time trending indicators and scores for content prioritization
- Enhanced UI with trending badges, engagement metrics, and story clusters
- Historical tracking for trend analysis and reporting

## IMPLEMENTATION PHASES:

### Phase 1: Core Engagement Tracking (Month 2)
1. **Enhanced Article Model**
   - Add engagement_metrics JSON field for source-specific metrics
   - Add trending_score and is_trending boolean fields
   - Add cross_source_coverage counter
   - Track engagement velocity (change over time)

2. **Source-Specific Metrics Collection**
   - YouTube: views, likes, comments, duration
   - Reddit: upvotes, comments, awards, upvote_ratio
   - Hugging Face: downloads, likes, discussions
   - GitHub: stars, forks, issues, release downloads
   - ArXiv: citation hints, Twitter mentions (future)
   - HackerNews: points, comments, ranking

### Phase 2: Trending Detection (Month 3)
1. **Velocity Algorithms**
   - Calculate engagement rate per hour since publication
   - Compare against historical baselines for each source
   - Weight by source-specific factors (channel size, subreddit activity)

2. **Cross-Source Correlation**
   - Detect same story across multiple sources using embeddings
   - Track time delay between sources (primary vs secondary coverage)
   - Calculate "story importance" based on source count

### Phase 3: UI Integration (Month 3-4)
1. **Trending Indicators**
   - 🔥 Fire emoji for trending content (velocity > 2x baseline)
   - 📈 Trending up arrow with velocity percentage
   - Source count badges for multi-source stories

2. **Story Clusters**
   - Grouped view for related articles
   - Primary source attribution
   - Timeline view of story propagation

## DATA MODEL:

### Enhanced Article Model
```python
class Article(BaseModel):
    # Existing fields...
    
    # Engagement tracking
    engagement_metrics: dict = Field(default_factory=dict)
    """
    Source-specific engagement data:
    {
        "views": 45000,           # YouTube views
        "likes": 1200,            # YouTube likes
        "upvotes": 234,          # Reddit/HN score
        "comments": 89,          # Comments count
        "stars_today": 156,      # GitHub stars gained
        "downloads_24h": 9800,   # HF model downloads
        "awards": ["gold", "silver"],  # Reddit awards
        "upvote_ratio": 0.95,    # Reddit engagement quality
        "velocity": 4.5,         # Engagement growth rate
        "baseline_velocity": 1.2 # Historical average for comparison
    }
    """
    
    # Trending indicators
    is_trending: bool = False
    trending_score: float = Field(default=0.0, ge=0, le=100)
    trending_reason: str | None = None  # "high_velocity", "multi_source", "viral"
    
    # Cross-source tracking
    cross_source_coverage: int = 0  # Number of sources covering this story
    story_cluster_id: UUID | None = None  # Links related articles
    is_primary_source: bool = True  # First to report the story
    related_articles: list[UUID] = Field(default_factory=list)
```

### Story Cluster Model
```python
class StoryCluster(BaseModel):
    """Represents a major story covered by multiple sources."""
    
    cluster_id: UUID
    title: str  # AI-generated unified title
    primary_article_id: UUID  # First/original source
    article_ids: list[UUID]  # All related articles
    
    # Timeline tracking
    first_seen: datetime
    last_updated: datetime
    timeline: list[dict]  # [{source, timestamp, article_id}]
    
    # Metrics
    total_engagement: dict  # Aggregated metrics
    source_count: int
    importance_score: float  # Based on coverage and engagement
    
    # AI-generated summary
    unified_summary: str
    key_developments: list[str]
    conflicting_info: list[str] | None
```

## TRENDING ALGORITHMS:

### Velocity Calculation
```python
class TrendingCalculator:
    def calculate_velocity(self, article: Article, hours_since_publish: float) -> float:
        """Calculate engagement velocity with decay factor."""
        metrics = article.engagement_metrics
        
        # Get primary engagement metric by source
        engagement = self._get_primary_metric(article.source, metrics)
        
        # Apply time decay (engagement typically slows)
        decay_factor = 1 / (1 + 0.1 * hours_since_publish)
        
        # Calculate hourly rate
        hourly_rate = engagement / max(hours_since_publish, 1)
        
        # Apply decay
        velocity = hourly_rate * decay_factor
        
        return velocity
    
    def is_trending(self, article: Article) -> tuple[bool, str]:
        """Determine if article is trending and why."""
        velocity = article.engagement_metrics.get('velocity', 0)
        baseline = article.engagement_metrics.get('baseline_velocity', 1)
        
        # High velocity (2x normal)
        if velocity > baseline * 2:
            return True, "high_velocity"
        
        # Multi-source coverage
        if article.cross_source_coverage >= 3:
            return True, "multi_source"
        
        # Viral threshold (source-specific)
        if self._is_viral(article):
            return True, "viral"
        
        return False, None
```

### Source-Specific Baselines
```python
ENGAGEMENT_BASELINES = {
    "youtube": {
        "views_per_hour": {
            "small_channel": 500,    # <100k subs
            "medium_channel": 2000,  # 100k-1M subs
            "large_channel": 10000   # >1M subs
        }
    },
    "reddit": {
        "r/LocalLLaMA": {
            "upvotes_per_hour": 25,
            "comments_per_hour": 5
        }
    },
    "huggingface": {
        "downloads_per_day": 100,
        "trending_threshold": 1000
    }
}
```

## CROSS-SOURCE STORY DETECTION:

### Clustering Algorithm
```python
class StoryClustering:
    def __init__(self, similarity_threshold: float = 0.85):
        self.threshold = similarity_threshold
        
    async def cluster_articles(
        self, 
        articles: list[Article], 
        time_window: timedelta = timedelta(hours=48)
    ) -> list[StoryCluster]:
        """Group related articles into story clusters."""
        clusters = []
        processed = set()
        
        for article in articles:
            if article.id in processed:
                continue
                
            # Find similar articles within time window
            similar = await self._find_similar_articles(
                article, 
                articles, 
                time_window
            )
            
            if len(similar) >= 2:  # At least 2 sources
                cluster = self._create_cluster(article, similar)
                clusters.append(cluster)
                processed.update([a.id for a in similar])
        
        return clusters
    
    def _calculate_importance(self, cluster: StoryCluster) -> float:
        """Calculate story importance score."""
        factors = {
            'source_count': min(cluster.source_count / 5, 1.0) * 0.3,
            'total_engagement': min(cluster.total_engagement / 10000, 1.0) * 0.3,
            'source_diversity': self._source_diversity_score(cluster) * 0.2,
            'time_span': min(24 / self._hours_span(cluster), 1.0) * 0.2
        }
        return sum(factors.values()) * 100
```

## PRIMARY SOURCE DISCOVERY:

### Automatic Source Chain Detection
When secondary sources (Reddit, HN, YouTube) mention primary sources, the system automatically:
1. Extracts primary source references
2. Fetches the original content
3. Links both articles bidirectionally

```python
class PrimarySourceExtractor:
    """Extract and fetch primary sources mentioned in secondary coverage."""
    
    # Known primary sources and their patterns
    SOURCE_PATTERNS = {
        'openai': {
            'patterns': ['OpenAI announced', 'OpenAI released', 'openai.com'],
            'rss_feed': 'https://openai.com/index/rss.xml',
            'keywords': ['GPT', 'DALL-E', 'Whisper']
        },
        'anthropic': {
            'patterns': ['Anthropic announced', 'Claude', 'anthropic.com'],
            'rss_feed': 'https://www.anthropic.com/index.xml',
            'keywords': ['Claude', 'Constitutional AI']
        },
        'deepmind': {
            'patterns': ['DeepMind', 'Gemini', 'deepmind.com'],
            'rss_feed': 'https://deepmind.com/blog/rss/',
            'keywords': ['Gemini', 'AlphaFold', 'Sparrow']
        },
        'meta': {
            'patterns': ['Meta AI', 'LLaMA', 'meta.ai'],
            'rss_feed': 'https://ai.facebook.com/blog/rss/',
            'keywords': ['LLaMA', 'Make-A-Video', 'Segment Anything']
        }
    }
    
    async def extract_primary_sources(self, article: Article) -> list[str]:
        """Extract potential primary sources from article content."""
        detected_sources = []
        
        # Search in title and content
        text = f"{article.title} {article.content}".lower()
        
        for source_id, config in self.SOURCE_PATTERNS.items():
            for pattern in config['patterns']:
                if pattern.lower() in text:
                    detected_sources.append(source_id)
                    break
            
            # Also check for product keywords
            for keyword in config['keywords']:
                if keyword.lower() in text:
                    detected_sources.append(source_id)
                    break
        
        return list(set(detected_sources))  # Remove duplicates
    
    async def fetch_primary_article(
        self, 
        source_id: str, 
        secondary_article: Article
    ) -> Article | None:
        """Fetch the primary source article related to secondary coverage."""
        config = self.SOURCE_PATTERNS.get(source_id)
        if not config:
            return None
        
        # Search recent articles from primary source
        # Look for matching announcement within 48 hour window
        time_window = timedelta(hours=48)
        cutoff_date = secondary_article.published_at - time_window
        
        # Query primary source articles
        primary_articles = await self._search_primary_source(
            source_id,
            config['rss_feed'],
            cutoff_date,
            secondary_article.title
        )
        
        if primary_articles:
            # Find best match using embeddings
            best_match = await self._find_best_match(
                secondary_article,
                primary_articles
            )
            return best_match
        
        return None
```

### Discovery Flow Implementation
```python
class SourceChainBuilder:
    """Build chains of related articles from primary to secondary sources."""
    
    async def process_secondary_article(self, article: Article) -> SourceChain:
        """Process secondary source article to find primary sources."""
        chain = SourceChain(secondary_article=article)
        
        # Only process community sources
        if article.source not in [ArticleSource.REDDIT, ArticleSource.HACKERNEWS, 
                                  ArticleSource.YOUTUBE]:
            return chain
        
        # Extract mentioned primary sources
        extractor = PrimarySourceExtractor()
        sources = await extractor.extract_primary_sources(article)
        
        for source_id in sources:
            # Fetch primary article
            primary = await extractor.fetch_primary_article(source_id, article)
            if primary:
                chain.add_primary_source(primary)
                
                # Update both articles with bidirectional links
                article.related_articles.append(primary.id)
                article.is_primary_source = False
                
                primary.related_articles.append(article.id)
                primary.cross_source_coverage += 1
        
        return chain
```

### Enhanced Story Cluster with Source Chains
```python
class EnhancedStoryCluster(StoryCluster):
    """Story cluster with primary source tracking."""
    
    # Source chain information
    source_chains: list[SourceChain] = Field(default_factory=list)
    primary_source_id: UUID | None = None  # The original announcement
    secondary_sources: list[UUID] = Field(default_factory=list)
    
    # Discovery metadata
    discovery_pattern: str | None = None  # How primary source was found
    time_to_primary: timedelta | None = None  # Time from secondary to finding primary
```

### UI Display for Source Chains
```html
<!-- Article Card with Source Chain Indicator -->
<div class="card reddit-post has-primary-source">
    <div class="source-chain-badge">
        <span class="chain-icon">🔗</span>
        <span class="chain-text">Primary source available</span>
    </div>
    
    <div class="card-content">
        <h3>Gemini 2.0 benchmarks are insane!</h3>
        <p class="card-meta">Reddit • 542 upvotes • 2h ago</p>
        
        <!-- Primary source link -->
        <div class="primary-source-link">
            <span class="link-icon">📰</span>
            <a href="#" class="primary-link">
                View original DeepMind announcement →
            </a>
        </div>
    </div>
</div>

<!-- Story cluster showing full chain -->
<div class="story-cluster with-source-chain">
    <div class="cluster-header">
        <h3>📰 Gemini 2.0 Launch</h3>
        <span class="chain-indicator">Primary → 6 discussions</span>
    </div>
    
    <div class="source-chain-timeline">
        <!-- Primary source first -->
        <div class="chain-item primary">
            <span class="time">4h ago</span>
            <span class="source">DeepMind Blog</span>
            <span class="badge">Original Announcement</span>
        </div>
        
        <!-- Arrow showing flow -->
        <div class="chain-flow">↓ Discovered by community</div>
        
        <!-- Secondary sources -->
        <div class="chain-item secondary">
            <span class="time">3h ago</span>
            <span class="source">r/LocalLLaMA</span>
            <span class="preview">"The benchmarks are incredible..."</span>
        </div>
    </div>
</div>
```

### Configuration
```python
# config/source_discovery.yaml
primary_sources:
  openai:
    name: "OpenAI"
    rss_feed: "https://openai.com/index/rss.xml"
    domains: ["openai.com"]
    products: ["GPT", "DALL-E", "Whisper", "ChatGPT"]
    
  anthropic:
    name: "Anthropic"
    rss_feed: "https://www.anthropic.com/index.xml"
    domains: ["anthropic.com"]
    products: ["Claude", "Constitutional AI"]

discovery_settings:
  time_window_hours: 48  # Look for primary sources within this window
  similarity_threshold: 0.80  # Minimum similarity for matching
  extract_from_sources: ["reddit", "hackernews", "youtube"]
```

## UI ENHANCEMENTS:

### Trending Content Row
```html
<!-- Trending Now Section -->
<section class="content-row trending-section">
    <h2 class="row-title">🔥 Trending Now</h2>
    <div class="cards-container">
        <!-- Trending Article Card -->
        <div class="card trending">
            <div class="trending-badge">
                <span class="fire-icon">🔥</span>
                <span class="velocity">+450%</span>
            </div>
            <div class="card-content">
                <h3>Gemini 2.0 Breaks Benchmarks</h3>
                <div class="engagement-stats">
                    <span class="stat">👁 125K views</span>
                    <span class="stat">💬 2.3K comments</span>
                    <span class="stat">📰 7 sources</span>
                </div>
            </div>
        </div>
    </div>
</section>
```

### Story Cluster View
```html
<!-- Major Story Cluster -->
<div class="story-cluster">
    <div class="cluster-header">
        <h3>📰 Gemini 2.0 Launch</h3>
        <span class="source-count">Covered by 7 sources</span>
    </div>
    
    <div class="cluster-timeline">
        <div class="timeline-item primary">
            <span class="time">2h ago</span>
            <span class="source">DeepMind Blog</span>
            <span class="badge">Original</span>
        </div>
        <div class="timeline-item">
            <span class="time">1h ago</span>
            <span class="source">r/LocalLLaMA</span>
            <span class="engagement">342 upvotes</span>
        </div>
        <div class="timeline-item">
            <span class="time">45m ago</span>
            <span class="source">YouTube - Fireship</span>
            <span class="engagement">125K views</span>
        </div>
    </div>
    
    <div class="cluster-summary">
        <p>Major announcement from DeepMind introducing Gemini 2.0 with significant improvements in reasoning and code generation...</p>
        <button class="expand-cluster">View all coverage →</button>
    </div>
</div>
```

### Engagement Indicators
```css
/* Trending indicators */
.trending-badge {
    position: absolute;
    top: 10px;
    right: 10px;
    background: linear-gradient(135deg, #ff6b6b, #ff8e53);
    color: white;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 14px;
    font-weight: bold;
    animation: pulse 2s infinite;
}

.engagement-stats {
    display: flex;
    gap: 12px;
    margin-top: 8px;
    font-size: 13px;
    opacity: 0.8;
}

.story-cluster {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 20px;
}
```

## PERFORMANCE CONSIDERATIONS:

### Caching Strategy
```python
CACHE_DURATIONS = {
    'engagement_metrics': 300,      # 5 minutes for live data
    'trending_scores': 600,         # 10 minutes
    'story_clusters': 1800,        # 30 minutes
    'velocity_baselines': 86400,   # 24 hours
}
```

### Database Optimization
- Index on `trending_score` for fast trending queries
- Materialized view for story clusters
- Partitioned tables for engagement history
- Background jobs for velocity calculations

### API Response Optimization
```python
class TrendingArticleResponse(BaseModel):
    """Optimized response for trending content."""
    articles: list[Article]
    clusters: list[StoryCluster]
    last_calculated: datetime
    cache_ttl: int = 300  # 5 minutes
```

## MONITORING & ANALYTICS:

### Metrics to Track
1. **Trending Accuracy**
   - False positive rate (marked trending but didn't sustain)
   - True positive rate (correctly identified viral content)
   - Average time to detect trending

2. **Engagement Patterns**
   - Peak engagement times by source
   - Velocity decay curves
   - Cross-source propagation time

3. **System Performance**
   - Calculation time for trending scores
   - Cache hit rates
   - API response times

### Dashboard Widgets
- Real-time trending feed
- Engagement velocity graphs
- Story propagation timeline
- Source performance comparison

## FUTURE ENHANCEMENTS:

### Phase 4: Predictive Trending (Month 6+)
- ML model to predict which articles will trend
- Early warning system for viral content
- Personalized trending based on user interests

### Phase 5: Sentiment Analysis (Month 7+)
- Track sentiment in comments/discussions
- Identify controversial topics
- Sentiment trends over time

### Phase 6: Influencer Tracking (Month 8+)
- Track key opinion leaders sharing content
- Influencer amplification factor
- Network effect analysis

## EXAMPLE IMPLEMENTATIONS:

### Example Trending Calculation
```python
# examples/trending/velocity_example.py
async def calculate_youtube_velocity(video_data: dict) -> float:
    """Example of YouTube-specific velocity calculation."""
    views = video_data['statistics']['viewCount']
    published = parse_iso8601(video_data['snippet']['publishedAt'])
    hours_old = (datetime.now(UTC) - published).total_seconds() / 3600
    
    # Get channel size for baseline
    channel_subs = video_data['channel']['subscriberCount']
    baseline = get_baseline_for_channel_size(channel_subs)
    
    # Calculate velocity with decay
    raw_velocity = views / max(hours_old, 1)
    decay = 1 / (1 + 0.1 * hours_old)
    velocity = raw_velocity * decay
    
    # Compare to baseline
    relative_velocity = velocity / baseline
    
    return relative_velocity
```

### Example Story Cluster
```json
{
  "cluster_id": "c3d4e5f6-1234-5678-9012-345678901234",
  "title": "OpenAI Announces GPT-5 with Reasoning Capabilities",
  "primary_article_id": "a1b2c3d4-1234-5678-9012-345678901234",
  "source_count": 5,
  "importance_score": 95.5,
  "timeline": [
    {
      "source": "OpenAI Blog",
      "timestamp": "2024-01-30T09:00:00Z",
      "article_id": "a1b2c3d4-1234-5678-9012-345678901234",
      "is_primary": true
    },
    {
      "source": "r/LocalLLaMA",
      "timestamp": "2024-01-30T09:45:00Z",
      "article_id": "b2c3d4e5-1234-5678-9012-345678901234",
      "engagement": {"upvotes": 1532, "comments": 289}
    }
  ],
  "total_engagement": {
    "views": 250000,
    "interactions": 15000,
    "shares": 3200
  }
}
```

## SUCCESS CRITERIA:

1. **Trending Detection**: Identify 90% of content that goes viral within 2 hours
2. **Story Clustering**: Correctly group 95% of related articles
3. **Performance**: Calculate trending scores for 1000 articles in <5 seconds
4. **User Engagement**: 50% increase in clicks on trending content
5. **API Efficiency**: Trending endpoint responds in <200ms with caching

This feature transforms the aggregator from a passive collector to an active trend spotter, helping users stay ahead of the AI news cycle.