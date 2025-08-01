# Entity Extraction & Story Clustering Specification

## Overview
Enhanced deduplication system that groups related articles into story clusters rather than marking them as duplicates. This enables tracking how news propagates from primary sources through community discussions.

## Core Concepts

### 1. Entity Extraction
Extract key entities from articles to enable cross-source matching:
- **Products**: GPT-4, Claude, Gemini, LLaMA, etc.
- **Companies**: OpenAI, Anthropic, Google, Meta, etc.
- **Versions**: v2.0, 3.5-turbo, etc.
- **Technologies**: RLHF, transformers, fine-tuning, etc.

### 2. Story Clustering
Group related articles about the same announcement/event:
- Primary announcement (DeepMind blog)
- Community discussions (Reddit, HackerNews)
- Analysis pieces (YouTube videos, blog posts)
- Follow-up coverage (tech news sites)

### 3. Cross-Source Linking
Track how information flows across sources:
- Reddit post → references → DeepMind blog
- YouTube video → discusses → arXiv paper
- HackerNews → links to → GitHub release

## Database Schema Changes

```sql
-- Add to articles table
ALTER TABLE articles ADD COLUMN entities JSONB;
ALTER TABLE articles ADD COLUMN story_cluster_id UUID;
ALTER TABLE articles ADD COLUMN article_type VARCHAR(50);
ALTER TABLE articles ADD COLUMN references_sources TEXT[];

-- Example entities JSON:
{
  "products": ["GPT-4", "ChatGPT"],
  "companies": ["OpenAI"],
  "versions": ["turbo", "v2"],
  "technologies": ["RLHF", "transformer"]
}
```

## Implementation Flow

### Phase 1: Entity Extraction
1. During article analysis, extract entities using regex/NLP
2. Store in structured JSON format
3. Enable entity-based search

### Phase 2: Smart Matching
1. When new article arrives, extract entities
2. Search for existing articles with overlapping entities
3. Calculate entity overlap score (70% threshold)
4. Determine if duplicate vs related

### Phase 3: Story Clustering
1. Create story_cluster_id for new stories
2. Add related articles to existing clusters
3. Track article types:
   - `primary_announcement`
   - `community_discussion`
   - `analysis`
   - `tutorial`

### Phase 4: Source Discovery
1. Extract URLs/domains mentioned in articles
2. Identify primary sources not in RSS feeds
3. Track reference chains
4. Suggest new RSS sources

## UI/UX Integration

### Article Display
```
[🔗 Part of story cluster with 5 related articles]

📰 DeepMind Announces Gemini 2.0
   Official announcement • 2 hours ago

💬 Reddit Discussion: "Gemini 2.0 benchmarks look insane"
   Community reaction • 1 hour ago
   → References: deepmind.com

📺 "Gemini 2.0 Explained" - AI Explained
   Video analysis • 30 min ago
   → Discusses: DeepMind announcement
```

### Story Cluster View
```
Story: Gemini 2.0 Release

Timeline:
├─ 9:00 AM - DeepMind Blog (Primary)
├─ 9:30 AM - Reddit r/LocalLLaMA (Discussion)
├─ 10:00 AM - HackerNews (Discussion)
├─ 11:00 AM - YouTube Analysis (Video)
└─ 2:00 PM - TechCrunch (News Coverage)

Key Entities:
• Product: Gemini 2.0
• Company: Google DeepMind
• Features: Multimodal, 1M context
```

## Benefits

1. **No False Duplicates**: Reddit discussions appear alongside primary sources
2. **Story Tracking**: See how news spreads across platforms
3. **Source Discovery**: Find new primary sources from secondary mentions
4. **Better Context**: Understand both official claims and community validation

## MVP vs Full Implementation

**MVP (Current)**: Simple deduplication prevents exact duplicates

**Full Implementation**:
- Entity extraction during analysis
- Story clustering algorithm
- Cross-source reference tracking
- Enhanced UI showing relationships
- Automatic source discovery

## Technical Components

1. **Entity Extractor Service**
   - Regex patterns for known entities
   - Extensible entity types
   - Caching for performance

2. **Story Clustering Service**
   - Entity overlap calculation
   - Temporal grouping (24-48hr window)
   - Cluster management

3. **Reference Tracker**
   - URL extraction from content
   - Domain identification
   - Source chain building

4. **UI Components**
   - Story cluster cards
   - Reference indicators
   - Timeline visualizations

## Future Enhancements

- ML-based entity recognition
- Automatic cluster naming
- Sentiment flow tracking
- Influence scoring (which sources drive discussion)
- API for story cluster queries