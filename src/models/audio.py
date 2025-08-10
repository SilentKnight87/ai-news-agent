"""
Audio-specific models for TTS pipeline.

This module defines data models for audio generation, streaming,
and queue processing.
"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


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
