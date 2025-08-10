-- Migration: Add indexes for search and filtering functionality
-- Run this in Supabase SQL Editor after the initial schema

-- Full-text search index for articles
CREATE INDEX IF NOT EXISTS idx_articles_fulltext 
ON articles USING gin(to_tsvector('english', title || ' ' || content));

-- Composite index for date and relevance filtering
CREATE INDEX IF NOT EXISTS idx_articles_date_relevance 
ON articles(published_at DESC, relevance_score DESC);

-- Source and date composite for source filtering
CREATE INDEX IF NOT EXISTS idx_articles_source_date 
ON articles(source, published_at DESC);

-- Categories GIN index for category filtering
CREATE INDEX IF NOT EXISTS idx_articles_categories 
ON articles USING gin(categories);

-- Digest date index for sorting
CREATE INDEX IF NOT EXISTS idx_digests_date 
ON daily_digests(digest_date DESC);

-- Composite index for digest_articles junction table
CREATE INDEX IF NOT EXISTS idx_digest_articles_composite 
ON digest_articles(digest_id, article_id);

-- Create a function for full-text search with ranking
CREATE OR REPLACE FUNCTION search_articles_fulltext(
    query_text TEXT,
    source_filter article_source DEFAULT NULL,
    max_results INT DEFAULT 20,
    skip_results INT DEFAULT 0
) RETURNS TABLE (
    id UUID,
    source_id TEXT,
    source article_source,
    title TEXT,
    content TEXT,
    url TEXT,
    author TEXT,
    published_at TIMESTAMP WITH TIME ZONE,
    fetched_at TIMESTAMP WITH TIME ZONE,
    summary TEXT,
    relevance_score REAL,
    categories TEXT[],
    key_points TEXT[],
    embedding vector(384),
    is_duplicate BOOLEAN,
    duplicate_of UUID,
    rank REAL,
    total_count BIGINT
) 
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    WITH ranked_results AS (
        SELECT 
            a.*,
            ts_rank(to_tsvector('english', a.title || ' ' || a.content), 
                    plainto_tsquery('english', query_text)) as search_rank,
            COUNT(*) OVER() as result_count
        FROM articles a
        WHERE to_tsvector('english', a.title || ' ' || a.content) @@ 
              plainto_tsquery('english', query_text)
          AND (source_filter IS NULL OR a.source = source_filter)
          AND a.is_duplicate = FALSE
        ORDER BY search_rank DESC, a.published_at DESC
        LIMIT max_results OFFSET skip_results
    )
    SELECT 
        r.id,
        r.source_id,
        r.source,
        r.title,
        r.content,
        r.url,
        r.author,
        r.published_at,
        r.fetched_at,
        r.summary,
        r.relevance_score,
        r.categories,
        r.key_points,
        r.embedding,
        r.is_duplicate,
        r.duplicate_of,
        r.search_rank,
        r.result_count
    FROM ranked_results r;
END;
$$;

-- Create a function to get source statistics
CREATE OR REPLACE FUNCTION get_sources_metadata()
RETURNS TABLE (
    source_name article_source,
    article_count BIGINT,
    last_published TIMESTAMP WITH TIME ZONE,
    avg_relevance_score NUMERIC
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        a.source as source_name,
        COUNT(*)::BIGINT as article_count,
        MAX(a.published_at) as last_published,
        ROUND(AVG(a.relevance_score)::NUMERIC, 2) as avg_relevance_score
    FROM articles a
    WHERE a.is_duplicate = FALSE
    GROUP BY a.source
    ORDER BY a.source;
END;
$$;