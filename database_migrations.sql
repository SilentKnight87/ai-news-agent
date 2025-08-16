-- Database Performance Optimization Migration
-- Execute these commands in Supabase SQL Editor or via psql

-- =============================================================================
-- CRITICAL: Missing Foreign Key Indexes (Performance Impact: HIGH)
-- =============================================================================

-- 1. Index for articles.duplicate_of foreign key
-- Fixes: Table `public.articles` has a foreign key `articles_duplicate_of_fkey` without a covering index
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_articles_duplicate_of 
ON public.articles(duplicate_of) 
WHERE duplicate_of IS NOT NULL;

-- 2. Index for audio_processing_queue.digest_id foreign key  
-- Fixes: Table `public.audio_processing_queue` has a foreign key `audio_processing_queue_digest_id_fkey` without a covering index
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audio_queue_digest_id 
ON public.audio_processing_queue(digest_id);

-- 3. Index for digest_articles.article_id foreign key
-- Fixes: Table `public.digest_articles` has a foreign key `digest_articles_article_id_fkey` without a covering index
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_digest_articles_article_id 
ON public.digest_articles(article_id);

-- =============================================================================
-- PERFORMANCE: Remove Unused Indexes (Resource Waste: LOW)
-- =============================================================================

-- Remove unused indexes identified by Supabase advisors
-- These indexes have never been used and consume maintenance overhead
DROP INDEX CONCURRENTLY IF EXISTS idx_articles_fetched_at;
DROP INDEX CONCURRENTLY IF EXISTS idx_audio_queue_status;

-- =============================================================================
-- OPTIMIZATION: Query-Specific Indexes (Performance Impact: MEDIUM)
-- =============================================================================

-- Composite index for common article filtering patterns
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_articles_relevance_published 
ON public.articles(relevance_score DESC, published_at DESC) 
WHERE is_duplicate = false;

-- Index for audio queue processing (replacement for removed status index)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audio_queue_pending 
ON public.audio_processing_queue(status, created_at) 
WHERE status = 'pending';

-- =============================================================================
-- SECURITY: RLS Policy Fixes (Performance + Security Impact: HIGH)
-- =============================================================================

-- Enable RLS on audio_processing_queue table (currently disabled)
ALTER TABLE public.audio_processing_queue ENABLE ROW LEVEL SECURITY;

-- Add RLS policy for service role access
CREATE POLICY "Audio queue managed by service role" 
ON public.audio_processing_queue FOR ALL 
TO service_role USING (true) WITH CHECK (true);

-- =============================================================================
-- RLS PERFORMANCE: Fix Auth Function Re-evaluation
-- =============================================================================

-- NOTE: These policies need to be updated to use (SELECT auth.uid()) instead of auth.uid()
-- This prevents re-evaluation of auth functions for each row

-- Daily Digests RLS Policy Optimization
-- Find and update policy: "Digests can be managed by service role"
-- Replace: auth.uid() with: (SELECT auth.uid())

-- Digest Articles RLS Policy Optimization  
-- Find and update policy: "Digest articles can be managed by service role"
-- Replace: auth.uid() with: (SELECT auth.uid())

-- =============================================================================
-- VECTOR SEARCH OPTIMIZATION
-- =============================================================================

-- Optimize vector index for better performance based on dataset size
ALTER INDEX idx_articles_embedding SET (lists = 50);

-- =============================================================================
-- VERIFICATION QUERIES
-- =============================================================================

-- Check that indexes were created successfully
SELECT 
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes 
WHERE indexname IN (
    'idx_articles_duplicate_of',
    'idx_audio_queue_digest_id', 
    'idx_digest_articles_article_id',
    'idx_articles_relevance_published',
    'idx_audio_queue_pending'
)
ORDER BY tablename, indexname;

-- Verify RLS is enabled
SELECT schemaname, tablename, rowsecurity 
FROM pg_tables 
WHERE tablename = 'audio_processing_queue';

-- Check for remaining performance issues
-- Run Supabase performance advisors again after applying changes