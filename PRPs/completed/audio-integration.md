# Audio Integration Specification

## FEATURE:

- Complete text-to-speech pipeline integration for daily digest audio generation
- ElevenLabs AI voice synthesis with high-quality natural speech output
- Supabase Storage integration for audio file management and CDN delivery
- Audio streaming endpoints with browser compatibility and progressive download
- Multiple voice options with personality matching for different content types
- Audio player controls with progress tracking, playback speed, and playlist functionality
- Background audio processing with queue management and retry mechanisms
- Audio caching and compression optimization for bandwidth efficiency
- Mobile-optimized audio playback with offline capability preparation
- Accessibility features including audio transcripts and playback controls

## AUDIO INTEGRATION TIERS:

### MVP Audio Features (Core TTS Pipeline):

1. **Digest Audio Generation**
   - Automatic audio generation during daily digest creation workflow
   - ElevenLabs API integration with voice selection and quality optimization
   - Audio file processing: MP3 format, 64kbps for bandwidth efficiency
   - Supabase Storage upload with proper file naming and metadata
   - Database integration: audio_url field in daily_digests table
   - Implementation: Async processing to avoid blocking digest generation
   
2. **Audio Streaming API**
   - `GET /api/digests/{id}/audio` - Stream audio file with proper headers
   - `GET /api/digests/{id}/audio/info` - Audio metadata (duration, size, format)
   - `POST /api/digests/{id}/regenerate-audio` - Manual audio regeneration
   - Range request support for progressive download and seeking
   - Content-Type and Cache-Control headers for browser optimization
   - Implementation: FastAPI streaming responses with proper MIME types

3. **Audio Storage Management**
   - Supabase Storage bucket configuration with CDN optimization
   - File naming convention: `digest-{digest_id}-{timestamp}.mp3`
   - Automatic cleanup of old audio files (30-day retention)
   - Storage quota monitoring and alerting
   - Backup strategy for audio files
   - Implementation: Async file operations with error handling and retries

### Tier 1: Enhanced Audio Experience

**Advanced Voice Options:**
- Multiple ElevenLabs voice profiles for content variety
- Voice selection based on digest theme (news vs technical vs community)
- SSML integration for improved pronunciation and pacing
- Custom voice training for brand consistency
- A/B testing for voice preference optimization

**Audio Player Features:**
```typescript
interface AudioPlayer {
  // Playback controls
  play(): void;
  pause(): void;
  seek(time: number): void;
  setPlaybackRate(rate: number): void; // 0.5x to 2x speed
  
  // Progress tracking
  currentTime: number;
  duration: number;
  buffered: TimeRanges;
  
  // Playlist functionality
  loadPlaylist(digests: Digest[]): void;
  next(): void;
  previous(): void;
  shuffle(): void;
}
```

**Audio Analytics:**
- Playback completion rates per digest
- Most popular playback speeds
- User engagement patterns (skip rates, replay rates)
- Device and browser compatibility metrics

### Tier 2: Production Audio Features

**Offline Capability:**
- Service Worker integration for audio caching
- Progressive Web App audio download for offline listening
- Local storage management for cached audio files
- Sync status indicators for downloaded content

**Advanced Processing:**
- Audio normalization for consistent volume levels
- Background noise reduction and audio enhancement
- Chapter markers for long digests with topic sections
- Automated transcript generation from audio (speech-to-text)

## IMPLEMENTATION DETAILS:

### ElevenLabs Integration:
```python
class TTSProcessor:
    def __init__(self):
        self.client = ElevenLabsClient(api_key=settings.ELEVENLABS_API_KEY)
        self.voice_profiles = {
            "news": "21m00Tcm4TlvDq8ikWAM",      # Professional news voice
            "technical": "AZnzlk1XvdvUeBnXmlld",  # Clear technical voice  
            "community": "EXAVITQu4vr4xnSDxMaL"   # Friendly community voice
        }
    
    async def generate_audio(self, text: str, voice_type: str = "news") -> bytes:
        voice_id = self.voice_profiles.get(voice_type, "news")
        
        try:
            audio = await self.client.generate(
                text=text,
                voice=Voice(voice_id=voice_id),
                model="eleven_multilingual_v2",
                output_format="mp3_44100_128"  # High quality for initial generation
            )
            
            # Compress for web delivery
            compressed_audio = await self._compress_audio(audio)
            return compressed_audio
            
        except ElevenLabsError as e:
            logger.error(f"TTS generation failed: {e}")
            raise AudioGenerationError(f"Failed to generate audio: {e}")
```

### Supabase Storage Integration:
```python
class AudioStorageManager:
    def __init__(self):
        self.storage = supabase.storage.from_("audio-digests")
    
    async def upload_audio(self, digest_id: str, audio_data: bytes) -> str:
        filename = f"digest-{digest_id}-{int(time.time())}.mp3"
        
        try:
            result = await self.storage.upload(
                path=filename,
                file=audio_data,
                file_options={
                    "content-type": "audio/mpeg",
                    "cache-control": "public, max-age=3600"
                }
            )
            
            # Get public URL
            public_url = self.storage.get_public_url(filename)
            return public_url
            
        except Exception as e:
            logger.error(f"Audio upload failed: {e}")
            raise AudioStorageError(f"Failed to store audio: {e}")
```

### Audio Streaming Endpoint:
```python
@router.get("/api/digests/{digest_id}/audio")
async def stream_digest_audio(
    digest_id: str,
    request: Request,
    range: str = Header(None)
):
    digest = await get_digest_by_id(digest_id)
    if not digest or not digest.audio_url:
        raise HTTPException(404, "Audio not found")
    
    # Handle range requests for seeking
    if range:
        return await stream_audio_range(digest.audio_url, range)
    
    return StreamingResponse(
        stream_audio_file(digest.audio_url),
        media_type="audio/mpeg",
        headers={
            "Accept-Ranges": "bytes",
            "Cache-Control": "public, max-age=3600",
            "Content-Disposition": f'inline; filename="digest-{digest_id}.mp3"'
        }
    )
```

### Database Schema Updates:
```sql
-- Add audio fields to daily_digests table
ALTER TABLE daily_digests ADD COLUMN audio_url TEXT;
ALTER TABLE daily_digests ADD COLUMN audio_duration INTEGER; -- seconds
ALTER TABLE daily_digests ADD COLUMN audio_size INTEGER;     -- bytes
ALTER TABLE daily_digests ADD COLUMN voice_type VARCHAR(50) DEFAULT 'news';
ALTER TABLE daily_digests ADD COLUMN audio_generated_at TIMESTAMP WITH TIME ZONE;

-- Create audio processing queue table
CREATE TABLE audio_processing_queue (
    id SERIAL PRIMARY KEY,
    digest_id INTEGER REFERENCES daily_digests(id),
    status VARCHAR(20) DEFAULT 'pending', -- pending, processing, completed, failed
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processed_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_audio_queue_status ON audio_processing_queue(status, created_at);
```

## PERFORMANCE REQUIREMENTS:

### Audio Generation:
- TTS processing: < 30 seconds for typical digest (500-1000 words)
- File compression: < 5 seconds additional processing time
- Storage upload: < 10 seconds for compressed audio files
- Queue processing: Handle up to 10 concurrent audio generations

### Audio Streaming:
- Initial audio response: < 500ms for streaming start
- Progressive download: Support range requests for seeking
- CDN caching: 1-hour cache for generated audio files
- Bandwidth optimization: 64kbps MP3 for mobile, 128kbps for desktop

### Storage Management:
- Daily cleanup job for expired audio files
- Storage quota monitoring with 80% threshold alerts
- Automatic retry mechanism for failed uploads
- Backup sync to secondary storage location

## SUCCESS CRITERIA:

- [ ] Digest audio automatically generated during digest creation
- [ ] ElevenLabs integration produces high-quality natural speech
- [ ] Audio files stored in Supabase Storage with proper metadata
- [ ] Streaming endpoint supports range requests and progressive download
- [ ] Audio player works across all major browsers and mobile devices
- [ ] Background processing doesn't block digest generation workflow
- [ ] Storage management handles cleanup and quota monitoring
- [ ] Error handling covers all failure scenarios with proper logging
- [ ] Performance targets met for generation and streaming
- [ ] User experience is seamless from digest creation to audio playback

## VALIDATION CHECKLIST:

### Audio Quality:
- [ ] Generated speech sounds natural and professional
- [ ] Pronunciation is accurate for technical terms
- [ ] Audio levels are consistent across different digests
- [ ] No artifacts or glitches in generated audio files
- [ ] Multiple voice options available and selectable

### Technical Integration:
- [ ] Audio generation completes within 30-second target
- [ ] Supabase Storage integration handles uploads reliably
- [ ] Streaming endpoint supports all major browsers
- [ ] Range requests work correctly for audio seeking
- [ ] Error handling covers network failures and API limits

### User Experience:
- [ ] Audio playback starts quickly (< 500ms)
- [ ] Progress tracking and seeking work smoothly
- [ ] Playback speed controls function correctly
- [ ] Mobile audio playback works without issues
- [ ] Offline capabilities prepare for future PWA features