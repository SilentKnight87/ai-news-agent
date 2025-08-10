"""
Audio streaming API endpoints.

This module provides endpoints for audio streaming, metadata,
and regeneration of digest audio.
"""

import logging
from typing import Annotated, AsyncGenerator

import httpx
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from fastapi.responses import StreamingResponse

from ..models.audio import AudioInfoResponse
from ..services.audio_queue import get_audio_queue
from .dependencies import get_supabase_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/digests", tags=["audio"])


async def stream_audio_content(url: str, chunk_size: int = 8192) -> AsyncGenerator[bytes, None]:
    """
    Stream audio content from URL.
    
    Args:
        url: URL to stream from.
        chunk_size: Size of chunks to stream.
        
    Yields:
        bytes: Audio chunks.
    """
    async with httpx.AsyncClient() as client:
        async with client.stream("GET", url) as response:
            response.raise_for_status()
            async for chunk in response.aiter_bytes(chunk_size):
                yield chunk


@router.get("/{digest_id}/audio")
async def stream_digest_audio(
    digest_id: str,
    request: Request,
    supabase: Annotated[any, Depends(get_supabase_client)],
    range: str = Header(None)
):
    """
    Stream audio with range request support.
    
    Args:
        digest_id: ID of the digest.
        request: FastAPI request object.
        range: Range header for partial content.
        supabase: Supabase client.
        
    Returns:
        StreamingResponse: Audio stream.
        
    Raises:
        HTTPException: If audio not found.
    """
    # Get digest
    result = supabase.table("daily_digests").select("*").eq("id", digest_id).single().execute()
    digest = result.data
    
    if not digest or not digest.get("audio_url"):
        raise HTTPException(404, "Audio not found")
    
    # Prepare headers
    headers = {
        "Accept-Ranges": "bytes",
        "Content-Type": "audio/mpeg",
        "Cache-Control": "public, max-age=3600"
    }
    
    # Handle range requests for seeking
    audio_size = digest.get("audio_size", 0)
    if range and audio_size > 0:
        # Parse range header
        try:
            range_start = int(range.split("=")[1].split("-")[0])
            headers["Content-Range"] = f"bytes {range_start}-{audio_size-1}/{audio_size}"
            headers["Content-Length"] = str(audio_size - range_start)
            status_code = 206
        except:
            headers["Content-Length"] = str(audio_size) if audio_size else None
            status_code = 200
    else:
        headers["Content-Length"] = str(audio_size) if audio_size else None
        status_code = 200
    
    # Remove None values from headers
    headers = {k: v for k, v in headers.items() if v is not None}
    
    return StreamingResponse(
        stream_audio_content(digest["audio_url"]),
        status_code=status_code,
        headers=headers,
        media_type="audio/mpeg"
    )


@router.get("/{digest_id}/audio/info")
async def get_audio_info(
    digest_id: str,
    supabase: Annotated[any, Depends(get_supabase_client)]
) -> AudioInfoResponse:
    """
    Get audio metadata for a digest.
    
    Args:
        digest_id: ID of the digest.
        supabase: Supabase client.
        
    Returns:
        AudioInfoResponse: Audio metadata.
        
    Raises:
        HTTPException: If audio not found.
    """
    # Get digest
    result = supabase.table("daily_digests").select("*").eq("id", digest_id).single().execute()
    digest = result.data
    
    if not digest or not digest.get("audio_url"):
        raise HTTPException(404, "Audio not found")
    
    return AudioInfoResponse(
        audio_url=digest["audio_url"],
        duration_seconds=digest.get("audio_duration", 0),
        file_size_bytes=digest.get("audio_size", 0),
        voice_type=digest.get("voice_type", "news"),
        generated_at=digest.get("audio_generated_at", digest["created_at"])
    )


@router.post("/{digest_id}/regenerate-audio")
async def regenerate_audio(
    digest_id: str,
    voice_type: str = "news"
):
    """
    Manually trigger audio regeneration.
    
    Args:
        digest_id: ID of the digest.
        voice_type: Voice type to use.
        
    Returns:
        dict: Success message.
    """
    audio_queue = get_audio_queue()
    
    success = await audio_queue.queue_audio_generation(
        digest_id=digest_id,
        text=None,  # Will fetch from digest
        voice_type=voice_type,
        force=True
    )
    
    if success:
        return {"message": "Audio regeneration queued", "digest_id": digest_id}
    else:
        raise HTTPException(500, "Failed to queue audio regeneration")