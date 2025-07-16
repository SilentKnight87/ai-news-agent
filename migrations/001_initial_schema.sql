-- Initial schema for AI News Aggregator
-- Run in Supabase SQL Editor

-- Enable pgvector extension for vector similarity search
CREATE EXTENSION IF NOT EXISTS vector;

-- Enable uuid extension for UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create enum for article sources
CREATE TYPE article_source AS ENUM ('arxiv', 'hackernews', 'rss');

-- Create articles table with vector embedding support
CREATE TABLE articles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_id TEXT NOT NULL,
    source article_source NOT NULL,
    title TEXT NOT NULL CHECK (length(title) > 0),
    content TEXT NOT NULL,
    url TEXT NOT NULL,
    author TEXT,
    published_at TIMESTAMP WITH TIME ZONE NOT NULL,
    fetched_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    -- AI-generated fields
    summary TEXT,
    relevance_score REAL CHECK (relevance_score >= 0 AND relevance_score <= 100),
    categories TEXT[] DEFAULT '{}',
    key_points TEXT[] DEFAULT '{}',
    
    -- Vector embedding for similarity search (384 dimensions for all-MiniLM-L6-v2)
    embedding vector(384),
    
    -- Deduplication tracking
    is_duplicate BOOLEAN NOT NULL DEFAULT FALSE,
    duplicate_of UUID REFERENCES articles(id),
    
    -- Constraints
    UNIQUE(source, source_id),  -- Prevent duplicate source entries
    CHECK (NOT (is_duplicate = TRUE AND duplicate_of IS NULL))  -- Duplicates must reference original
);

-- Create daily_digests table
CREATE TABLE daily_digests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    digest_date DATE NOT NULL UNIQUE,
    summary_text TEXT NOT NULL CHECK (length(summary_text) <= 2000),
    total_articles_processed INTEGER NOT NULL,
    audio_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Create digest_articles junction table (many-to-many)
CREATE TABLE digest_articles (
    digest_id UUID REFERENCES daily_digests(id) ON DELETE CASCADE,
    article_id UUID REFERENCES articles(id) ON DELETE CASCADE,
    PRIMARY KEY (digest_id, article_id)
);

-- Create indexes for performance
CREATE INDEX idx_articles_published_at ON articles(published_at DESC);
CREATE INDEX idx_articles_source ON articles(source);
CREATE INDEX idx_articles_fetched_at ON articles(fetched_at DESC);
CREATE INDEX idx_articles_relevance_score ON articles(relevance_score DESC);
CREATE INDEX idx_articles_is_duplicate ON articles(is_duplicate);
CREATE INDEX idx_articles_url ON articles(url);

-- Create HNSW index for vector similarity search (after inserting ~1000 vectors for optimal performance)
-- For initial development, use IVFFlat which works with fewer vectors
CREATE INDEX idx_articles_embedding ON articles USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Function to find similar articles based on embedding similarity
CREATE OR REPLACE FUNCTION match_articles(
    query_embedding vector(384),
    match_threshold float DEFAULT 0.85,
    match_count int DEFAULT 5
) RETURNS TABLE (
    id uuid,
    url text,
    title text,
    similarity float,
    published_at timestamp with time zone
) 
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        articles.id,
        articles.url,
        articles.title,
        1 - (articles.embedding <=> query_embedding) as similarity,
        articles.published_at
    FROM articles
    WHERE articles.embedding IS NOT NULL
        AND 1 - (articles.embedding <=> query_embedding) > match_threshold
        AND articles.is_duplicate = FALSE  -- Only match non-duplicates
    ORDER BY articles.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- Function to get articles for daily digest (top articles by relevance)
CREATE OR REPLACE FUNCTION get_top_articles_for_digest(
    since_date timestamp with time zone DEFAULT NOW() - INTERVAL '24 hours',
    article_limit int DEFAULT 10
) RETURNS TABLE (
    id uuid,
    title text,
    summary text,
    relevance_score real,
    source article_source,
    url text,
    published_at timestamp with time zone
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        articles.id,
        articles.title,
        articles.summary,
        articles.relevance_score,
        articles.source,
        articles.url,
        articles.published_at
    FROM articles
    WHERE articles.published_at >= since_date
        AND articles.is_duplicate = FALSE
        AND articles.relevance_score IS NOT NULL
        AND articles.relevance_score > 50  -- Only include relevant articles
    ORDER BY articles.relevance_score DESC, articles.published_at DESC
    LIMIT article_limit;
END;
$$;

-- Row Level Security (RLS) policies
ALTER TABLE articles ENABLE ROW LEVEL SECURITY;
ALTER TABLE daily_digests ENABLE ROW LEVEL SECURITY;
ALTER TABLE digest_articles ENABLE ROW LEVEL SECURITY;

-- Allow read access to articles for anonymous users
CREATE POLICY "Articles are viewable by everyone" ON articles
    FOR SELECT USING (true);

-- Allow insert/update for service role only
CREATE POLICY "Articles can be inserted by service role" ON articles
    FOR INSERT WITH CHECK (auth.role() = 'service_role');

CREATE POLICY "Articles can be updated by service role" ON articles
    FOR UPDATE USING (auth.role() = 'service_role');

-- Similar policies for other tables
CREATE POLICY "Digests are viewable by everyone" ON daily_digests
    FOR SELECT USING (true);

CREATE POLICY "Digests can be managed by service role" ON daily_digests
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Digest articles are viewable by everyone" ON digest_articles
    FOR SELECT USING (true);

CREATE POLICY "Digest articles can be managed by service role" ON digest_articles
    FOR ALL USING (auth.role() = 'service_role');

-- Create a view for articles with their categories as a readable format
CREATE VIEW articles_view AS
SELECT 
    id,
    source_id,
    source,
    title,
    content,
    url,
    author,
    published_at,
    fetched_at,
    summary,
    relevance_score,
    array_to_string(categories, ', ') as categories_text,
    array_to_string(key_points, '; ') as key_points_text,
    is_duplicate,
    duplicate_of
FROM articles
WHERE is_duplicate = FALSE
ORDER BY published_at DESC;