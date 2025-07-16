# Tier 2 Features & Post-MVP Enhancements

## Overview
This document outlines Tier 2 data sources and advanced features to be implemented after successful MVP deployment. These features assume a stable MVP with 50+ daily active users and proven deduplication/summarization pipeline.

## Timeline
- **Month 2-3**: Tier 1 Primary Sources
- **Month 3-4**: Tier 2 Community Sources  
- **Month 4+**: Advanced Features & Monetization

---

## Tier 2 Data Sources

### Reddit Integration (Month 3)

#### Requirements
- **Cost**: ~$0.24 per 1000 API requests
- **Rate Limit**: 60 requests/minute with OAuth
- **Implementation**: PRAW (Python Reddit API Wrapper)

#### Target Subreddits
```python
REDDIT_SOURCES = {
    'primary': [
        'MachineLearning',    # 3M+ members, research papers
        'LocalLLaMA',         # 300k+ members, open models
        'singularity',        # 2M+ members, AGI discussions
    ],
    'secondary': [
        'OpenAI',             # Company-specific
        'artificial',         # General AI discussion
        'deeplearning',       # Technical discussions
        'MLQuestions',        # Q&A format
        'computervision',     # Specific domain
        'LanguageTechnology', # NLP focused
    ]
}
```

#### Implementation Details
```python
# src/fetchers/reddit_fetcher.py
import asyncpraw
from datetime import datetime, timedelta

class RedditFetcher(BaseFetcher):
    def __init__(self, settings):
        self.reddit = asyncpraw.Reddit(
            client_id=settings.reddit_client_id,
            client_secret=settings.reddit_client_secret,
            user_agent="AI-News-Aggregator/1.0"
        )
        self.subreddits = REDDIT_SOURCES['primary']
        
    async def fetch(self) -> List[Article]:
        articles = []
        since = datetime.utcnow() - timedelta(hours=24)
        
        for subreddit_name in self.subreddits:
            subreddit = await self.reddit.subreddit(subreddit_name)
            
            # Get hot, new, and top posts
            async for submission in subreddit.hot(limit=25):
                if datetime.fromtimestamp(submission.created_utc) > since:
                    # Filter by score and engagement
                    if submission.score > 50 or submission.num_comments > 10:
                        articles.append(self._parse_submission(submission))
        
        return articles
    
    def _should_include(self, submission) -> bool:
        """Filter logic for relevance"""
        ai_keywords = {'ai', 'ml', 'llm', 'gpt', 'neural', 'model', 'transformer'}
        title_lower = submission.title.lower()
        return any(keyword in title_lower for keyword in ai_keywords)
```

#### Cost Optimization
- Cache user profiles to avoid repeated lookups
- Batch API requests where possible
- Store submission IDs to avoid re-fetching
- Use webhooks for real-time updates (future)

### YouTube Integration (Month 3-4)

#### Requirements
- **Quota**: 10,000 units/day (search = 100 units)
- **Implementation**: YouTube Data API v3
- **Cost**: Free but heavily limited

#### Target Channels
```python
YOUTUBE_CHANNELS = {
    'technical': {
        'UCZHmQk67mSJgfCCTn7xBfew': 'Two Minute Papers',
        'UCm3PvSzM5kR4VO8gEj1LhCA': 'Yannic Kilcher',
        'UCAMpWwlHg7-6IaZ7qYWwqPA': 'AI Explained',
    },
    'news_updates': {
        'UCjRbWgUdqmtcp-2BdI1JYsA': 'Matt Wolfe',
        'UCbfYPyITQ-7l4upoX8nvctg': 'Two Minute Papers',
        'UCqSQm_6TUObpgd9Mc3cvmVQ': 'The AI Breakdown',
    },
    'tutorials': {
        'UCNNaW6E6SRM0q-fJ1r-Y0MA': 'Nicholas Renotte',
        'UCg1u_rq0J2Z-CMCgcviOyJw': 'Abhishek Thakur',
    }
}
```

#### Implementation Strategy
```python
# src/fetchers/youtube_fetcher.py
from googleapiclient.discovery import build

class YouTubeFetcher(BaseFetcher):
    def __init__(self, settings):
        self.youtube = build('youtube', 'v3', 
                           developerKey=settings.youtube_api_key)
        self.quota_tracker = QuotaTracker(daily_limit=10000)
        
    async def fetch(self) -> List[Article]:
        articles = []
        
        # Optimize quota usage - batch channel requests
        channel_ids = ','.join(YOUTUBE_CHANNELS['technical'].keys())
        
        # Cost: 3 units for channels.list
        response = self.youtube.channels().list(
            part='contentDetails',
            id=channel_ids,
            maxResults=50
        ).execute()
        
        # Get recent videos from uploads playlist
        for channel in response['items']:
            playlist_id = channel['contentDetails']['relatedPlaylists']['uploads']
            
            # Cost: 3 units per playlist request
            videos = self._get_playlist_videos(playlist_id, max_results=5)
            
            for video in videos:
                if self._is_ai_related(video):
                    articles.append(self._parse_video(video))
        
        return articles
```

#### Quota Management
- Track daily quota usage in database
- Prioritize high-value channels
- Cache video metadata for 7 days
- Use RSS feeds as backup when quota exhausted

### Twitter/X Integration (Month 4+)

#### Note: Expensive - Consider Carefully
- **Cost**: $100/month for basic API access
- **Alternative**: Monitor specific accounts via RSS/web scraping

#### Target Lists
```yaml
ai_researchers:
  - @karpathy (Andrej Karpathy)
  - @sama (Sam Altman)  
  - @GaryMarcus (Gary Marcus)
  - @ylecun (Yann LeCun)
  - @goodfellow_ian (Ian Goodfellow)

ai_companies:
  - @OpenAI
  - @AnthropicAI
  - @DeepMind
  - @HuggingFace
  - @weights_biases
```

---

## Advanced Features (Post-MVP)

### 1. Personalization Engine (Month 3)

#### User Preferences
```python
class UserPreferences(BaseModel):
    user_id: str
    interests: List[str]  # ["computer-vision", "nlp", "robotics"]
    sources: Dict[str, bool]  # {"arxiv": True, "reddit": False}
    relevance_threshold: float = 70.0
    digest_time: str = "08:00"  # User's preferred time
    digest_timezone: str = "UTC"
```

#### Implementation
- Track article interactions (clicks, saves, shares)
- Build user interest profile using collaborative filtering
- Personalize relevance scoring based on history
- Custom digest timing per user

### 2. Topic Clustering & Trend Detection (Month 4)

#### Clustering Implementation
```python
# src/services/clustering.py
from sklearn.cluster import HDBSCAN
import numpy as np

class TopicClusterer:
    def __init__(self, min_cluster_size=5):
        self.clusterer = HDBSCAN(
            min_cluster_size=min_cluster_size,
            metric='cosine'
        )
    
    async def cluster_articles(self, articles: List[Article]) -> Dict[int, List[Article]]:
        # Extract embeddings
        embeddings = np.array([a.embedding for a in articles])
        
        # Perform clustering
        cluster_labels = self.clusterer.fit_predict(embeddings)
        
        # Group articles by cluster
        clusters = {}
        for idx, label in enumerate(cluster_labels):
            if label != -1:  # Ignore noise
                clusters.setdefault(label, []).append(articles[idx])
        
        # Generate cluster summaries using PydanticAI
        for cluster_id, cluster_articles in clusters.items():
            clusters[cluster_id] = await self._generate_cluster_summary(cluster_articles)
        
        return clusters
```

#### Trend Detection
- Track topic velocity (mentions over time)
- Identify emerging topics (sudden increase in mentions)
- Alert users about trending topics in their interests
- Generate trend reports

### 3. Advanced Deduplication (Month 3)

#### Cross-Source Story Tracking
```python
class StoryCluster(BaseModel):
    """Track the same story across multiple sources"""
    cluster_id: str
    primary_article: Article
    related_articles: List[Article]
    sources: List[str]  # Which sources covered it
    timeline: List[Dict[str, Any]]  # How story evolved
    key_facts: List[str]  # Extracted facts
    contradictions: List[str]  # Conflicting information
```

#### Implementation
- Build story graphs connecting related articles
- Extract and reconcile facts across sources
- Identify conflicting information
- Present unified view with all perspectives

### 4. Smart Notifications (Month 4)

#### Notification Types
1. **Breaking News**: Major AI announcements
2. **Threshold Alerts**: Articles > 95 relevance score
3. **Topic Alerts**: New articles in subscribed topics
4. **Weekly Trends**: What you missed this week

#### Delivery Channels
- Email (primary)
- Slack integration
- Discord bot
- Mobile push (future)

### 5. API & Developer Features (Month 5)

#### Public API
```python
# API Endpoints
GET /api/v1/articles
GET /api/v1/articles/{id}
GET /api/v1/topics/trending
GET /api/v1/digest/{date}
POST /api/v1/search

# Webhooks
POST /webhooks/article.created
POST /webhooks/digest.ready
POST /webhooks/trend.detected
```

#### Developer Features
- API key management
- Rate limiting per key
- Usage analytics
- Webhook subscriptions
- Custom RSS feeds

### 6. Enterprise Features (Month 6+)

#### Team Accounts
- Shared article collections
- Team-wide topic subscriptions
- Collaborative filtering
- Admin dashboard

#### Advanced Analytics
- Topic coverage heatmaps
- Source reliability scoring
- Reading time analytics
- Team engagement metrics

#### Compliance & Security
- GDPR compliance tools
- Data retention policies
- Audit logs
- SSO integration

---

## Monetization Strategy

### Tier Structure
```yaml
Free Tier:
  - 3 news sources (ArXiv, HN, RSS)
  - Daily digest
  - 7-day history
  - Basic deduplication

Pro ($19/month):
  - All Tier 1 sources
  - Personalization
  - 30-day history
  - Advanced search
  - Email/Slack alerts
  - Priority support

Team ($99/month):
  - Everything in Pro
  - 5 team members
  - Shared collections
  - API access (10k calls/month)
  - Custom sources
  - Analytics dashboard

Enterprise (Custom):
  - Unlimited users
  - All Tier 2 sources
  - Custom integrations
  - SLA guarantee
  - Dedicated support
  - On-premise option
```

### Revenue Projections
- Month 3: 100 free users
- Month 6: 500 free, 50 pro ($950 MRR)
- Month 12: 2000 free, 200 pro, 10 teams ($4,790 MRR)

---

## Technical Improvements

### 1. Performance Optimization

#### Caching Strategy
```python
# Redis for hot data
CACHE_LAYERS = {
    'embeddings': 7 * 24 * 3600,     # 7 days
    'articles': 24 * 3600,           # 1 day
    'digests': 30 * 24 * 3600,       # 30 days
    'user_prefs': 3600,              # 1 hour
}
```

#### Database Optimization
- Partition articles table by month
- Create materialized views for common queries
- Implement read replicas for scaling
- Use TimescaleDB for time-series data

### 2. Infrastructure Scaling

#### Queue System (Replace Cron)
```python
# Celery + Redis for task queue
CELERY_BEAT_SCHEDULE = {
    'fetch-articles': {
        'task': 'tasks.fetch_articles',
        'schedule': crontab(minute='*/15'),
    },
    'generate-digest': {
        'task': 'tasks.generate_digest',
        'schedule': crontab(hour=8, minute=0),
    },
    'cluster-topics': {
        'task': 'tasks.cluster_topics',
        'schedule': crontab(minute=0),  # Hourly
    },
}
```

#### Microservices Architecture
- Fetcher Service (handles all sources)
- AI Service (embeddings, summaries)
- Notification Service
- API Gateway
- Frontend BFF (Backend for Frontend)

### 3. ML/AI Enhancements

#### Better Embeddings
- Upgrade to larger models (e.g., all-mpnet-base-v2)
- Fine-tune embeddings on AI/ML corpus
- Multi-lingual support

#### Advanced Summarization
- Extract key quotes
- Generate TL;DR + detailed summary
- Identify paper contributions
- Extract code snippets

#### Quality Scoring
```python
class QualityScorer:
    """Score article quality beyond relevance"""
    
    def score(self, article: Article) -> float:
        factors = {
            'source_authority': self._score_source(article.source),
            'engagement': self._score_engagement(article),
            'recency': self._score_recency(article.published_at),
            'uniqueness': self._score_uniqueness(article),
            'technical_depth': self._score_depth(article.content),
        }
        
        # Weighted average
        weights = {
            'source_authority': 0.25,
            'engagement': 0.20,
            'recency': 0.20,
            'uniqueness': 0.20,
            'technical_depth': 0.15,
        }
        
        return sum(factors[k] * weights[k] for k in factors)
```

---

## Implementation Priority

### Phase 1 (Month 2-3)
1. ✅ Add Tier 1 RSS sources
2. ✅ Implement basic personalization
3. ✅ Add email notifications

### Phase 2 (Month 3-4)
1. 🔄 Reddit integration
2. 🔄 YouTube integration (limited)
3. 🔄 Topic clustering
4. 🔄 Pro tier launch

### Phase 3 (Month 4-5)
1. 📅 Advanced deduplication
2. 📅 Trend detection
3. 📅 API development
4. 📅 Team features

### Phase 4 (Month 6+)
1. 📅 Enterprise features
2. 📅 Twitter/X integration
3. 📅 Custom sources
4. 📅 ML improvements

---

## Success Metrics

### User Engagement
- Daily Active Users (DAU)
- Articles clicked per user
- Digest open rate
- API usage

### Technical Metrics
- Deduplication accuracy (>95%)
- Summary quality score
- API response time (<200ms)
- Source uptime (>99%)

### Business Metrics
- Free → Pro conversion (>5%)
- Monthly Recurring Revenue
- Churn rate (<5%)
- Customer Acquisition Cost

---

## Risk Mitigation

### API Dependency
- **Risk**: Reddit/Twitter API changes
- **Mitigation**: Abstract fetcher interface, multiple sources

### Cost Overruns
- **Risk**: Embedding/LLM costs explode
- **Mitigation**: Strict rate limiting, caching, batch processing

### Legal/Copyright
- **Risk**: Content ownership issues
- **Mitigation**: Clear attribution, summary only, link to source

### Technical Debt
- **Risk**: MVP shortcuts hurt scaling
- **Mitigation**: Refactor before Phase 2, maintain test coverage

---

## Conclusion

Tier 2 features transform the MVP into a comprehensive AI news intelligence platform. Focus on user value and revenue generation while maintaining system reliability. Each feature should be validated with user feedback before full implementation.