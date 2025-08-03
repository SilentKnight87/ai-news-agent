"""
Text-to-Speech service using ElevenLabs API.

This module provides text-to-speech capabilities for converting
daily digests into audio format for consumption while commuting.
"""

import asyncio
import hashlib
import logging
from pathlib import Path

import aiofiles
import httpx
from pydantic import BaseModel, Field

from ..config import get_settings
from .rate_limiter import get_rate_limit_manager

logger = logging.getLogger(__name__)


class TTSConfig(BaseModel):
    """Configuration for text-to-speech generation."""

    voice_id: str = Field(
        "21m00Tcm4TlvDq8ikWAM",  # Default ElevenLabs voice (Rachel)
        description="ElevenLabs voice ID"
    )
    model_id: str = Field(
        "eleven_monolingual_v1",
        description="ElevenLabs model ID"
    )
    stability: float = Field(0.5, ge=0.0, le=1.0, description="Voice stability")
    similarity_boost: float = Field(0.5, ge=0.0, le=1.0, description="Similarity boost")
    style: float = Field(0.0, ge=0.0, le=1.0, description="Style setting")
    use_speaker_boost: bool = Field(True, description="Enable speaker boost")


class TTSResult(BaseModel):
    """Result of text-to-speech generation."""

    text_hash: str = Field(..., description="Hash of the input text")
    audio_file_path: str = Field(..., description="Path to generated audio file")
    duration_seconds: float | None = Field(None, description="Audio duration")
    file_size_bytes: int = Field(..., description="File size in bytes")
    generation_time_seconds: float = Field(..., description="Time taken to generate")


class TTSService:
    """
    Text-to-Speech service using ElevenLabs API.
    
    Provides high-quality voice synthesis for daily digest summaries
    with caching and rate limiting.
    """

    def __init__(self, output_dir: str = "audio_outputs"):
        """
        Initialize TTS service.
        
        Args:
            output_dir: Directory to store generated audio files.
        """
        self.settings = get_settings()
        self.config = TTSConfig()
        self.rate_limiter = get_rate_limit_manager()

        # Create output directory
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        # ElevenLabs API configuration
        self.base_url = "https://api.elevenlabs.io/v1"
        self.headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": self.settings.elevenlabs_api_key or ""
        }

        logger.info(f"TTS service initialized with output dir: {self.output_dir}")

    def _generate_text_hash(self, text: str) -> str:
        """
        Generate a hash for the input text for caching.
        
        Args:
            text: Input text to hash.
            
        Returns:
            str: SHA256 hash of the text.
        """
        return hashlib.sha256(text.encode('utf-8')).hexdigest()[:16]

    def _get_cache_path(self, text_hash: str) -> Path:
        """
        Get the cache file path for a text hash.
        
        Args:
            text_hash: Hash of the input text.
            
        Returns:
            Path: Path to the cached audio file.
        """
        return self.output_dir / f"tts_{text_hash}.mp3"

    async def is_cached(self, text: str) -> bool:
        """
        Check if audio for this text is already cached.
        
        Args:
            text: Input text to check.
            
        Returns:
            bool: True if cached audio exists.
        """
        text_hash = self._generate_text_hash(text)
        cache_path = self._get_cache_path(text_hash)
        return cache_path.exists()

    async def get_cached_result(self, text: str) -> TTSResult | None:
        """
        Get cached TTS result if available.
        
        Args:
            text: Input text.
            
        Returns:
            Optional[TTSResult]: Cached result or None if not found.
        """
        text_hash = self._generate_text_hash(text)
        cache_path = self._get_cache_path(text_hash)

        if cache_path.exists():
            file_size = cache_path.stat().st_size
            return TTSResult(
                text_hash=text_hash,
                audio_file_path=str(cache_path),
                file_size_bytes=file_size,
                generation_time_seconds=0.0  # Cached, no generation time
            )

        return None

    async def generate_speech(
        self,
        text: str,
        voice_id: str | None = None,
        use_cache: bool = True
    ) -> TTSResult:
        """
        Generate speech from text using ElevenLabs API.
        
        Args:
            text: Text to convert to speech.
            voice_id: Optional voice ID override.
            use_cache: Whether to use cached results.
            
        Returns:
            TTSResult: Generated audio result.
            
        Raises:
            Exception: If TTS generation fails.
        """
        if not self.settings.elevenlabs_api_key:
            raise ValueError("ElevenLabs API key not configured")

        # Check cache first
        if use_cache:
            cached_result = await self.get_cached_result(text)
            if cached_result:
                logger.info(f"Using cached TTS result for text hash: {cached_result.text_hash}")
                return cached_result

        start_time = asyncio.get_event_loop().time()
        text_hash = self._generate_text_hash(text)

        try:
            logger.info(f"Generating TTS for text hash: {text_hash}")

            # Rate limit the request
            await self.rate_limiter.wait_and_acquire("elevenlabs", tokens=1)

            # Prepare request
            voice_id = voice_id or self.config.voice_id
            url = f"{self.base_url}/text-to-speech/{voice_id}"

            payload = {
                "text": text,
                "model_id": self.config.model_id,
                "voice_settings": {
                    "stability": self.config.stability,
                    "similarity_boost": self.config.similarity_boost,
                    "style": self.config.style,
                    "use_speaker_boost": self.config.use_speaker_boost
                }
            }

            # Make API request
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(url, json=payload, headers=self.headers)
                response.raise_for_status()

                # Save audio to file
                cache_path = self._get_cache_path(text_hash)
                async with aiofiles.open(cache_path, 'wb') as f:
                    await f.write(response.content)

                generation_time = asyncio.get_event_loop().time() - start_time
                file_size = len(response.content)

                logger.info(
                    f"TTS generated successfully: {file_size} bytes in {generation_time:.2f}s"
                )

                return TTSResult(
                    text_hash=text_hash,
                    audio_file_path=str(cache_path),
                    file_size_bytes=file_size,
                    generation_time_seconds=generation_time
                )

        except httpx.HTTPStatusError as e:
            logger.error(f"ElevenLabs API error: {e.response.status_code} - {e.response.text}")
            raise Exception(f"TTS generation failed: {e.response.status_code}")
        except Exception as e:
            logger.error(f"TTS generation failed: {e}")
            raise

    async def generate_digest_audio(self, digest_text: str) -> TTSResult:
        """
        Generate audio for a daily digest with optimizations.
        
        Args:
            digest_text: Digest text to convert.
            
        Returns:
            TTSResult: Generated audio result.
        """
        # Truncate if too long for TTS
        max_chars = self.settings.max_digest_chars
        if len(digest_text) > max_chars:
            logger.warning(f"Truncating digest from {len(digest_text)} to {max_chars} chars")
            digest_text = digest_text[:max_chars] + "..."

        # Add intro/outro for better listening experience
        enhanced_text = f"""
        Good morning! Here's your AI news digest for today.
        
        {digest_text}
        
        That's all for today's AI developments. Stay curious!
        """

        return await self.generate_speech(enhanced_text.strip())

    async def list_available_voices(self) -> list[dict]:
        """
        Get list of available voices from ElevenLabs.
        
        Returns:
            list[dict]: List of available voices.
        """
        if not self.settings.elevenlabs_api_key:
            raise ValueError("ElevenLabs API key not configured")

        try:
            await self.rate_limiter.wait_and_acquire("elevenlabs", tokens=1)

            url = f"{self.base_url}/voices"
            headers = {"xi-api-key": self.settings.elevenlabs_api_key}

            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()

                data = response.json()
                return data.get("voices", [])

        except Exception as e:
            logger.error(f"Failed to fetch voices: {e}")
            return []

    def get_cache_stats(self) -> dict:
        """
        Get statistics about the audio cache.
        
        Returns:
            dict: Cache statistics.
        """
        if not self.output_dir.exists():
            return {"total_files": 0, "total_size_bytes": 0}

        audio_files = list(self.output_dir.glob("tts_*.mp3"))
        total_size = sum(f.stat().st_size for f in audio_files)

        return {
            "total_files": len(audio_files),
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "cache_directory": str(self.output_dir)
        }

    async def cleanup_old_cache(self, keep_latest: int = 10) -> int:
        """
        Clean up old cached audio files.
        
        Args:
            keep_latest: Number of latest files to keep.
            
        Returns:
            int: Number of files deleted.
        """
        if not self.output_dir.exists():
            return 0

        audio_files = list(self.output_dir.glob("tts_*.mp3"))

        # Sort by modification time (newest first)
        audio_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)

        # Delete old files
        files_to_delete = audio_files[keep_latest:]
        deleted_count = 0

        for file_path in files_to_delete:
            try:
                file_path.unlink()
                deleted_count += 1
                logger.debug(f"Deleted old cache file: {file_path}")
            except Exception as e:
                logger.warning(f"Failed to delete {file_path}: {e}")

        if deleted_count > 0:
            logger.info(f"Cleaned up {deleted_count} old cache files")

        return deleted_count


# Global TTS service instance
_tts_service: TTSService | None = None


def get_tts_service() -> TTSService:
    """
    Get the global TTS service instance.
    
    Returns:
        TTSService: Global TTS service.
    """
    global _tts_service
    if _tts_service is None:
        _tts_service = TTSService()
    return _tts_service


async def generate_digest_audio(digest_text: str) -> TTSResult:
    """
    Convenience function to generate audio for a digest.
    
    Args:
        digest_text: Digest text to convert.
        
    Returns:
        TTSResult: Generated audio result.
    """
    tts_service = get_tts_service()
    return await tts_service.generate_digest_audio(digest_text)
