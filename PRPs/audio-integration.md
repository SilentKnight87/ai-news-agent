name: "Audio Integration - TTS Pipeline and Streaming PRP"
description: |

## Purpose
Implement complete text-to-speech pipeline integration for daily digest audio generation with ElevenLabs voice synthesis, Supabase Storage for file management, and streaming endpoints for browser playback.

## Core Principles
1. **Async First**: Use existing async patterns for non-blocking audio generation
2. **Background Processing**: Integrate with existing scheduler for queue management
3. **Storage Integration**: Use Supabase Storage for CDN-optimized delivery
4. **Streaming Performance**: FastAPI StreamingResponse for progressive download
5. **Error Resilience**: Retry mechanisms for external API failures

---

## Goal
Complete the audio integration pipeline by connecting the existing TTS service to the digest generation workflow, implementing Supabase Storage for audio files, and creating streaming endpoints for frontend consumption.

## Why
- **User Engagement**: Enable digest consumption while commuting/exercising
- **Accessibility**: Audio format serves visually impaired users
- **Content Reach**: 40% of users prefer audio content (industry avg)
- **Technical Debt**: audio_url column exists but is unused

## What
Audio pipeline with:
- Automatic TTS generation during digest creation (non-blocking)
- Supabase Storage integration for audio file hosting
- Streaming endpoints with range request support
- Background processing queue for audio generation
- Multiple voice profiles for content variety
- Audio metadata tracking (duration, size, voice type)

### Success Criteria
- [ ] Audio files generated automatically for new digests
- [ ] Audio generation doesn't block digest creation (< 1s added)
- [ ] Streaming starts within 500ms of request
- [ ] Range requests work for seeking/resume
- [ ] Failed generations retry automatically
- [ ] Storage cleanup removes files > 30 days old
- [ ] All tests pass with > 90% coverage

## All Needed Context

### Documentation & References
```yaml
# MUST READ - Include these in your context window
- file: src/services/tts.py
  why: Existing TTS service with ElevenLabs integration
  
- file: src/agents/digest_agent.py
  why: Digest generation workflow to integrate with
  
- file: src/services/scheduler.py
  why: Background task patterns for audio queue
  
- file: src/api/routes.py
  why: API patterns for streaming endpoints
  
- file: src/config.py
  why: Configuration patterns and env variables
  
- doc: https://docs.supabase.com/guides/storage
  section: Upload files from server-side
  critical: Proper bucket configuration and public URLs
  
- doc: https://fastapi.tiangolo.com/advanced/custom-response/#streamingresponse
  why: Streaming response patterns for audio delivery
  
- docfile: spec/audio-integration.md
  why: Complete specification with implementation details

# MCP Tool Documentation
- mcp: mcp__supabase__apply_migration
  why: Add missing audio columns to database
  
- mcp: mcp__supabase__execute_sql
  why: Verify migration and test queries
  
- mcp: mcp__context7__get-library-docs
  params: /elevenlabs/elevenlabs-python, topic="async,streaming"
  why: Async patterns for ElevenLabs integration
```

### Current Codebase Structure
```bash
src/
├── services/
│   ├── tts.py             # TTS service with ElevenLabs (exists)
│   ├── scheduler.py       # Background task scheduler
│   └── deduplication.py   # Service pattern reference
├── agents/
│   └── digest_agent.py    # Digest generation to modify
├── api/
│   ├── routes.py          # API endpoints
│   └── dependencies.py    # Dependency injection
└── repositories/
    └── articles.py        # Repository pattern
```

### Desired Structure with New Files
```bash
src/
├── services/
│   ├── tts.py             # Extended with async patterns
│   ├── audio_storage.py   # New: Supabase Storage service
│   └── audio_queue.py     # New: Background queue processor
├── api/
│   ├── routes.py          # Extended with audio endpoints
│   └── audio.py           # New: Audio-specific routes
├── tasks/
│   └── audio_tasks.py     # New: Background audio tasks
└── models/
    └── audio.py           # New: Audio-specific models
```

### Known Gotchas & Critical Context
```python
# CRITICAL: daily_digests.audio_url already exists
# No migration needed for basic audio_url storage
# But need additional columns for metadata

# CRITICAL: TTS service uses local file storage
# Current: audio_outputs/ directory
# Need to: Upload to Supabase after generation

# CRITICAL: ElevenLabs rate limits
# 10,000 characters/month on free tier
# Use caching and check text length before calling

# CRITICAL: Supabase Storage bucket setup
# Must create "audio-digests" bucket with public access
# File size limit: 50MB (plenty for audio)

# PATTERN: Background tasks use scheduler
# See fetch_articles_background() in routes.py
# Use similar pattern for audio generation

# PATTERN: Service initialization
# Services use singleton pattern with get_X_service()
# Follow same pattern for audio_storage service

# GOTCHA: StreamingResponse needs async generator
# Must use async file operations for streaming
```

## Implementation Blueprint

### Data Models
```python
# src/models/audio.py - Audio-specific models

from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

class AudioStatus(str, Enum):
    """Audio generation status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class AudioMetadata(BaseModel):
    """Audio file metadata."""
    duration_seconds: int
    file_size_bytes: int
    voice_type: str = "news"
    format: str = "mp3"
    bitrate: str = "64kbps"

class AudioGenerationTask(BaseModel):
    """Audio generation queue task."""
    digest_id: str
    text: str
    voice_type: str = "news"
    status: AudioStatus = AudioStatus.PENDING
    error_message: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    processed_at: datetime | None = None

class AudioInfoResponse(BaseModel):
    """Audio metadata API response."""
    audio_url: str
    duration_seconds: int
    file_size_bytes: int
    voice_type: str
    generated_at: datetime
```

### Task List

```yaml
Task 1: Database Schema Updates
EXECUTE via MCP:
  - mcp__supabase__apply_migration:
      name: "add_audio_metadata_columns"
      query: |
        -- Add missing audio metadata columns
        ALTER TABLE daily_digests 
        ADD COLUMN IF NOT EXISTS audio_duration INTEGER,
        ADD COLUMN IF NOT EXISTS audio_size INTEGER,
        ADD COLUMN IF NOT EXISTS voice_type VARCHAR(50) DEFAULT 'news',
        ADD COLUMN IF NOT EXISTS audio_generated_at TIMESTAMP WITH TIME ZONE;
        
        -- Create audio processing queue table
        CREATE TABLE IF NOT EXISTS audio_processing_queue (
            id SERIAL PRIMARY KEY,
            digest_id UUID REFERENCES daily_digests(id),
            status VARCHAR(20) DEFAULT 'pending',
            error_message TEXT,
            retry_count INTEGER DEFAULT 0,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            processed_at TIMESTAMP WITH TIME ZONE
        );
        
        -- Index for queue processing
        CREATE INDEX IF NOT EXISTS idx_audio_queue_status 
        ON audio_processing_queue(status, created_at);

Task 2: Create Supabase Storage Service
CREATE src/services/audio_storage.py:
  - PATTERN: Similar to existing service patterns
  - INTEGRATE: Supabase client dependency
  - METHODS: upload_audio(), get_audio_url(), delete_audio()
  - ERROR HANDLING: Retry on network failures

Task 3: Extend TTS Service for Async
MODIFY src/services/tts.py:
  - UPGRADE: Use AsyncElevenLabs client
  - ADD: Voice profile configuration
  - INTEGRATE: Audio compression for web delivery
  - PATTERN: Keep existing caching logic

Task 4: Create Audio Queue Processor
CREATE src/services/audio_queue.py:
  - PATTERN: Similar to deduplication service
  - METHODS: queue_audio_generation(), process_queue()
  - INTEGRATE: With scheduler for periodic processing
  - RETRY: Failed generations with exponential backoff

Task 5: Modify Digest Generation
MODIFY src/agents/digest_agent.py:
  - ADD: Queue audio generation after digest creation
  - PATTERN: Non-blocking - don't await audio
  - PRESERVE: Existing digest generation logic

Task 6: Create Audio Background Tasks
CREATE src/tasks/audio_tasks.py:
  - TASK: process_audio_queue() - runs every minute
  - TASK: cleanup_old_audio() - runs daily
  - INTEGRATE: With scheduler service

Task 7: Implement Audio Streaming Endpoints
CREATE src/api/audio.py:
  - GET /api/digests/{id}/audio - Stream with range support
  - GET /api/digests/{id}/audio/info - Metadata endpoint
  - POST /api/digests/{id}/regenerate-audio - Manual trigger
  - PATTERN: Use StreamingResponse

Task 8: Storage Cleanup Task
ADD to scheduler:
  - DAILY: Remove audio files > 30 days old
  - MONITOR: Storage quota usage
  - LOG: Cleanup statistics
```

### Per-Task Implementation Details

```python
# Task 2: Audio Storage Service
# src/services/audio_storage.py
import io
from pathlib import Path
from supabase import Client
import logging

logger = logging.getLogger(__name__)

class AudioStorageService:
    """Manages audio file storage in Supabase."""
    
    BUCKET_NAME = "audio-digests"
    
    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client
        self._ensure_bucket_exists()
    
    def _ensure_bucket_exists(self):
        """Ensure storage bucket exists."""
        try:
            buckets = self.supabase.storage.list_buckets()
            if not any(b["name"] == self.BUCKET_NAME for b in buckets):
                self.supabase.storage.create_bucket(
                    self.BUCKET_NAME,
                    options={"public": True}
                )
        except Exception as e:
            logger.error(f"Failed to ensure bucket: {e}")
    
    async def upload_audio(
        self, 
        digest_id: str, 
        audio_path: Path,
        metadata: dict
    ) -> str:
        """Upload audio file to Supabase Storage."""
        filename = f"digest-{digest_id}-{int(time.time())}.mp3"
        
        try:
            with open(audio_path, 'rb') as f:
                result = self.supabase.storage.from_(self.BUCKET_NAME).upload(
                    path=filename,
                    file=f,
                    file_options={
                        "content-type": "audio/mpeg",
                        "cache-control": "public, max-age=3600",
                        "x-upsert": "true"  # Overwrite if exists
                    }
                )
            
            # Get public URL
            public_url = self.supabase.storage.from_(self.BUCKET_NAME).get_public_url(filename)
            logger.info(f"Uploaded audio: {filename}")
            return public_url
            
        except Exception as e:
            logger.error(f"Audio upload failed: {e}")
            raise

# Task 3: Async TTS Service Updates
# Modify src/services/tts.py
from elevenlabs.client import AsyncElevenLabs
import aiofiles

class TTSService:
    def __init__(self, output_dir: str = "audio_outputs"):
        # ... existing init ...
        # Add async client
        self.async_client = AsyncElevenLabs(
            api_key=self.settings.elevenlabs_api_key
        )
        
        # Voice profiles for variety
        self.voice_profiles = {
            "news": "21m00Tcm4TlvDq8ikWAM",      # Rachel - professional
            "technical": "AZnzlk1XvdvUeBnXmlld",  # Adam - clear technical
            "community": "EXAVITQu4vr4xnSDxMaL"   # Bella - friendly
        }
    
    async def generate_speech_async(
        self,
        text: str,
        voice_type: str = "news",
        use_cache: bool = True
    ) -> TTSResult:
        """Async version of speech generation."""
        # Check cache first
        if use_cache:
            cached = await self.get_cached_result(text)
            if cached:
                return cached
        
        # Rate limit
        await self.rate_limiter.wait_and_acquire("elevenlabs", tokens=1)
        
        # Generate audio
        voice_id = self.voice_profiles.get(voice_type, self.voice_profiles["news"])
        
        audio = await self.async_client.text_to_speech.convert(
            text=text,
            voice_id=voice_id,
            model_id="eleven_multilingual_v2",
            output_format="mp3_44100_64"  # Lower bitrate for web
        )
        
        # Save to file
        text_hash = self._generate_text_hash(text)
        cache_path = self._get_cache_path(text_hash)
        
        async with aiofiles.open(cache_path, 'wb') as f:
            await f.write(audio)
        
        return TTSResult(
            text_hash=text_hash,
            audio_file_path=str(cache_path),
            file_size_bytes=len(audio),
            generation_time_seconds=0  # Track if needed
        )

# Task 5: Modify Digest Generation
# Add to src/agents/digest_agent.py
async def generate_digest(self, articles, digest_date, max_summary_length=2000):
    # ... existing digest generation ...
    
    # After creating digest, queue audio generation
    from ..services.audio_queue import get_audio_queue
    audio_queue = get_audio_queue()
    
    # Queue audio task (non-blocking)
    asyncio.create_task(
        audio_queue.queue_audio_generation(
            digest_id=str(digest.id),
            text=digest.summary_text,
            voice_type="news"  # Could vary by theme
        )
    )
    
    logger.info(f"Queued audio generation for digest {digest.id}")
    return digest

# Task 7: Audio Streaming Endpoints
# src/api/audio.py
from fastapi import APIRouter, HTTPException, Request, Header
from fastapi.responses import StreamingResponse
import httpx
from typing import AsyncGenerator

router = APIRouter(prefix="/digests", tags=["audio"])

async def stream_audio_content(url: str, chunk_size: int = 8192) -> AsyncGenerator[bytes, None]:
    """Stream audio content from URL."""
    async with httpx.AsyncClient() as client:
        async with client.stream("GET", url) as response:
            response.raise_for_status()
            async for chunk in response.aiter_bytes(chunk_size):
                yield chunk

@router.get("/{digest_id}/audio")
async def stream_digest_audio(
    digest_id: str,
    request: Request,
    range: str = Header(None),
    digest_repo: Annotated[DigestRepository, Depends(get_digest_repository)]
):
    """Stream audio with range request support."""
    digest = await digest_repo.get_by_id(digest_id)
    if not digest or not digest.audio_url:
        raise HTTPException(404, "Audio not found")
    
    headers = {
        "Accept-Ranges": "bytes",
        "Content-Type": "audio/mpeg",
        "Cache-Control": "public, max-age=3600"
    }
    
    # Handle range requests for seeking
    if range:
        # Parse range header
        range_start = int(range.split("=")[1].split("-")[0])
        headers["Content-Range"] = f"bytes {range_start}-{digest.audio_size-1}/{digest.audio_size}"
        headers["Content-Length"] = str(digest.audio_size - range_start)
        status_code = 206
    else:
        headers["Content-Length"] = str(digest.audio_size)
        status_code = 200
    
    return StreamingResponse(
        stream_audio_content(digest.audio_url),
        status_code=status_code,
        headers=headers,
        media_type="audio/mpeg"
    )

@router.post("/{digest_id}/regenerate-audio")
async def regenerate_audio(
    digest_id: str,
    voice_type: str = "news",
    audio_queue: Annotated[AudioQueueService, Depends(get_audio_queue)]
):
    """Manually trigger audio regeneration."""
    await audio_queue.queue_audio_generation(
        digest_id=digest_id,
        text=None,  # Will fetch from digest
        voice_type=voice_type,
        force=True
    )
    
    return {"message": "Audio regeneration queued", "digest_id": digest_id}
```

### Integration Points
```yaml
DATABASE:
  - migration: "Add audio metadata columns and queue table"
  - indexes: "Queue status index for efficient processing"
  
STORAGE:
  - bucket: "audio-digests" with public access
  - naming: "digest-{id}-{timestamp}.mp3"
  - cleanup: Daily task for > 30 day files
  
CONFIG:
  - add to: src/config.py
  - values: |
      AUDIO_GENERATION_ENABLED = bool(os.getenv('AUDIO_GENERATION_ENABLED', 'true'))
      AUDIO_RETENTION_DAYS = int(os.getenv('AUDIO_RETENTION_DAYS', '30'))
      AUDIO_MAX_RETRIES = int(os.getenv('AUDIO_MAX_RETRIES', '3'))
  
SCHEDULER:
  - add task: process_audio_queue (every minute)
  - add task: cleanup_old_audio (daily at 3am UTC)
  
ROUTES:
  - add to: src/main.py
  - pattern: app.include_router(audio.router, prefix="/api/v1")
```

## Validation Loop

### Level 1: Syntax & Style
```bash
cd ai-news-aggregator-agent
source .venv/bin/activate

# Check all modified files
ruff check src/services/tts.py src/services/audio_storage.py --fix
ruff check src/api/audio.py src/tasks/audio_tasks.py --fix
mypy src/services/audio_storage.py
mypy src/api/audio.py

# Expected: No errors
```

### Level 2: Database & Storage Validation
```bash
# Verify migration applied
mcp__supabase__execute_sql(
  query="SELECT column_name FROM information_schema.columns WHERE table_name = 'daily_digests';"
)
# Expected: See audio_duration, audio_size, voice_type columns

# Verify storage bucket
mcp__supabase__execute_sql(
  query="SELECT name FROM storage.buckets WHERE name = 'audio-digests';"
)
# Expected: audio-digests bucket exists
```

### Level 3: Unit Tests
```python
# CREATE tests/test_audio_integration.py
import pytest
from unittest.mock import Mock, patch, AsyncMock
from src.services.audio_storage import AudioStorageService
from src.services.tts import TTSService

@pytest.mark.asyncio
async def test_audio_upload():
    """Test audio file upload to Supabase."""
    mock_supabase = Mock()
    service = AudioStorageService(mock_supabase)
    
    # Mock upload response
    mock_supabase.storage.from_().upload.return_value = {"path": "test.mp3"}
    mock_supabase.storage.from_().get_public_url.return_value = "https://example.com/test.mp3"
    
    url = await service.upload_audio("digest-123", Path("test.mp3"), {})
    assert url == "https://example.com/test.mp3"

@pytest.mark.asyncio
async def test_tts_async_generation():
    """Test async TTS generation."""
    service = TTSService()
    
    with patch.object(service.async_client.text_to_speech, 'convert') as mock_convert:
        mock_convert.return_value = b"audio data"
        
        result = await service.generate_speech_async("Test text")
        assert result.file_size_bytes == 10
        assert Path(result.audio_file_path).exists()

@pytest.mark.asyncio
async def test_audio_streaming_endpoint(client):
    """Test audio streaming with range requests."""
    # Mock digest with audio
    mock_digest = Mock(audio_url="https://example.com/audio.mp3", audio_size=1000000)
    
    with patch('src.api.audio.get_digest_by_id', return_value=mock_digest):
        # Test full file request
        response = await client.get("/api/v1/digests/123/audio")
        assert response.status_code == 200
        assert response.headers["Accept-Ranges"] == "bytes"
        
        # Test range request
        response = await client.get(
            "/api/v1/digests/123/audio",
            headers={"Range": "bytes=1000-"}
        )
        assert response.status_code == 206
        assert "Content-Range" in response.headers

@pytest.mark.asyncio
async def test_audio_queue_retry():
    """Test audio queue retry on failure."""
    from src.services.audio_queue import AudioQueueService
    
    queue = AudioQueueService()
    
    # Mock TTS failure then success
    with patch.object(queue.tts_service, 'generate_speech_async') as mock_tts:
        mock_tts.side_effect = [Exception("API error"), Mock(audio_file_path="test.mp3")]
        
        await queue.process_queue()
        
        # Should retry and succeed
        assert mock_tts.call_count == 2
```

```bash
# Run tests
uv run pytest tests/test_audio_integration.py -v

# Expected: All tests pass
```

### Level 4: Integration Test
```bash
# Start service
uv run python -m src.main

# Create a test digest
curl -X POST http://localhost:8000/api/v1/webhook/fetch \
  -H "Content-Type: application/json" \
  -d '{"sources": ["hackernews"], "force": true}'

# Wait for digest generation
sleep 30

# Check latest digest has audio
curl http://localhost:8000/api/v1/digest/latest | jq '.digest.audio_url'
# Expected: Non-null audio URL

# Test audio streaming
AUDIO_URL=$(curl -s http://localhost:8000/api/v1/digest/latest | jq -r '.digest.id')
curl -I "http://localhost:8000/api/v1/digests/$AUDIO_URL/audio"
# Expected: 200 OK with audio/mpeg content-type

# Test range request (seeking)
curl -I -H "Range: bytes=1000-" "http://localhost:8000/api/v1/digests/$AUDIO_URL/audio"
# Expected: 206 Partial Content

# Check audio queue status
curl http://localhost:8000/api/v1/monitoring/audio-queue
# Expected: Shows completed tasks
```

## MCP Validation Commands
```yaml
# After implementation, validate with:

# 1. Check audio metadata populated
mcp__supabase__execute_sql:
  query: |
    SELECT id, audio_url, audio_duration, audio_size, voice_type
    FROM daily_digests
    WHERE audio_url IS NOT NULL
    LIMIT 5;

# 2. Check queue processing
mcp__supabase__execute_sql:
  query: |
    SELECT status, COUNT(*) 
    FROM audio_processing_queue
    GROUP BY status;

# 3. Verify storage usage
mcp__supabase__execute_sql:
  query: |
    SELECT 
      COUNT(*) as file_count,
      SUM(size) as total_bytes
    FROM storage.objects
    WHERE bucket_id = 'audio-digests';

# Expected: Files exist with reasonable sizes
```

## Final Validation Checklist
- [ ] All 8 tasks completed successfully
- [ ] Database migration applied (audio metadata columns)
- [ ] Supabase Storage bucket created and accessible
- [ ] Audio generated automatically for new digests
- [ ] Streaming endpoint works with range requests
- [ ] Background queue processes reliably
- [ ] Failed generations retry automatically
- [ ] Old audio files cleaned up by scheduled task
- [ ] No blocking during digest generation
- [ ] All tests pass: `uv run pytest tests/test_audio* -v`
- [ ] Manual integration test successful

---

## Anti-Patterns to Avoid
- ❌ Don't block digest generation waiting for audio
- ❌ Don't store audio files in database (use Storage)
- ❌ Don't skip retry logic for API failures
- ❌ Don't hardcode voice IDs - use config
- ❌ Don't stream from local files - use Supabase URLs
- ❌ Don't ignore ElevenLabs rate limits
- ❌ Don't process audio synchronously
- ❌ Don't forget cleanup of old files

## Performance Notes
1. **Non-blocking**: Audio generation must not delay digest creation
2. **Streaming**: Use async generators for efficient memory usage
3. **Caching**: TTS service already caches - preserve this
4. **Compression**: 64kbps MP3 for mobile bandwidth
5. **CDN**: Supabase Storage provides global CDN automatically

## Score: 9/10
High confidence due to:
- Existing TTS service provides solid foundation
- Clear integration points with digest generation
- Database schema partially ready (audio_url exists)
- Comprehensive patterns from existing services
- MCP tools for validation at each step

The 1-point deduction is for potential Supabase Storage configuration complexity that may require manual bucket setup.