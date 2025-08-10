"""
Tests for audio integration pipeline.

This module tests the TTS service, audio storage, queue processing,
and streaming endpoints.
"""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

from src.models.audio import AudioGenerationTask, AudioInfoResponse, AudioStatus
from src.services.audio_queue import AudioQueueService
from src.services.audio_storage import AudioStorageService
from src.services.tts import TTSResult, TTSService


@pytest.mark.asyncio
async def test_audio_storage_upload():
    """Test audio file upload to Supabase Storage."""
    # Mock Supabase client
    mock_supabase = Mock()
    mock_supabase.storage.list_buckets.return_value = []
    mock_supabase.storage.create_bucket.return_value = {"name": "audio-digests"}
    
    # Mock upload response
    mock_from = Mock()
    mock_from.upload.return_value = {"path": "test.mp3"}
    mock_from.get_public_url.return_value = "https://example.com/test.mp3"
    mock_supabase.storage.from_.return_value = mock_from
    
    # Create service and test upload
    service = AudioStorageService(mock_supabase)
    
    # Create a test file
    test_file = Path("test_audio.mp3")
    test_file.write_bytes(b"audio data")
    
    try:
        url = await service.upload_audio("digest-123", test_file, {})
        assert url == "https://example.com/test.mp3"
        mock_from.upload.assert_called_once()
    finally:
        test_file.unlink()


@pytest.mark.asyncio
async def test_tts_service_caching():
    """Test TTS service caching functionality."""
    service = TTSService(output_dir="test_audio_cache")
    
    # Test cache check
    text = "Test text for caching"
    is_cached = await service.is_cached(text)
    assert not is_cached
    
    # Generate and cache
    with patch.object(service, 'generate_speech') as mock_generate:
        mock_generate.return_value = TTSResult(
            text_hash="test_hash",
            audio_file_path="test.mp3",
            file_size_bytes=1000,
            generation_time_seconds=1.0
        )
        
        result = await service.generate_digest_audio(text)
        assert result.text_hash == "test_hash"
    
    # Clean up
    import shutil
    if Path("test_audio_cache").exists():
        shutil.rmtree("test_audio_cache")


@pytest.mark.asyncio
async def test_audio_queue_processing():
    """Test audio queue task processing."""
    queue = AudioQueueService()
    
    # Mock TTS service
    with patch.object(queue, 'tts_service') as mock_tts:
        mock_tts.generate_digest_audio = AsyncMock(
            return_value=TTSResult(
                text_hash="test_hash",
                audio_file_path="test.mp3",
                file_size_bytes=1000,
                generation_time_seconds=1.0
            )
        )
        
        # Mock storage upload
        with patch('src.services.audio_queue.get_audio_storage_service') as mock_storage:
            mock_storage.return_value.upload_audio = AsyncMock(
                return_value="https://example.com/audio.mp3"
            )
            
            # Mock Supabase client
            with patch('src.services.audio_queue.get_supabase_client') as mock_supabase:
                mock_table = Mock()
                mock_table.update.return_value.eq.return_value.execute.return_value = None
                mock_supabase.return_value.table.return_value = mock_table
                
                # Queue a task
                success = await queue.queue_audio_generation(
                    digest_id="test-digest",
                    text="Test digest text",
                    voice_type="news"
                )
                assert success
                
                # Process queue
                processed = await queue.process_queue()
                assert processed == 1
                
                # Check task status
                status = await queue.get_queue_status()
                assert status["completed"] == 1


@pytest.mark.asyncio
async def test_audio_generation_retry():
    """Test audio queue retry on failure."""
    queue = AudioQueueService()
    queue.max_retries = 2
    queue.retry_delay = 0  # No delay for testing
    
    # Create a task
    task = AudioGenerationTask(
        digest_id="test-digest",
        text="Test text",
        voice_type="news"
    )
    queue.queue.append(task)
    
    # Mock TTS failure then success
    with patch.object(queue, 'tts_service') as mock_tts:
        mock_tts.generate_digest_audio = AsyncMock(
            side_effect=[
                Exception("API error"),
                TTSResult(
                    text_hash="test_hash",
                    audio_file_path="test.mp3",
                    file_size_bytes=1000,
                    generation_time_seconds=1.0
                )
            ]
        )
        
        # Mock storage and database
        with patch('src.services.audio_queue.get_audio_storage_service') as mock_storage:
            mock_storage.return_value.upload_audio = AsyncMock(
                return_value="https://example.com/audio.mp3"
            )
            
            with patch('src.services.audio_queue.get_supabase_client') as mock_supabase:
                mock_table = Mock()
                mock_table.update.return_value.eq.return_value.execute.return_value = None
                mock_supabase.return_value.table.return_value = mock_table
                
                # Process task (should retry and succeed)
                await queue._process_task(task)
                
                # Should have called TTS twice
                assert mock_tts.generate_digest_audio.call_count == 2
                assert task.status == AudioStatus.COMPLETED


@pytest.mark.asyncio
async def test_audio_info_response():
    """Test audio info response model."""
    from datetime import datetime
    
    info = AudioInfoResponse(
        audio_url="https://example.com/audio.mp3",
        duration_seconds=120,
        file_size_bytes=1500000,
        voice_type="news",
        generated_at=datetime.utcnow()
    )
    
    assert info.audio_url == "https://example.com/audio.mp3"
    assert info.duration_seconds == 120
    assert info.file_size_bytes == 1500000
    assert info.voice_type == "news"
    assert isinstance(info.generated_at, datetime)


@pytest.mark.asyncio
async def test_audio_streaming_endpoint():
    """Test audio streaming endpoint with range requests."""
    from fastapi.testclient import TestClient
    from src.main import app
    
    client = TestClient(app)
    
    # Mock Supabase response
    with patch('src.api.audio.get_supabase_client') as mock_supabase:
        mock_result = Mock()
        mock_result.data = {
            "id": "test-digest",
            "audio_url": "https://example.com/audio.mp3",
            "audio_size": 1000000,
            "audio_duration": 120,
            "voice_type": "news",
            "created_at": "2024-01-01T00:00:00Z"
        }
        
        mock_supabase.return_value.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = mock_result
        
        # Mock audio streaming
        with patch('src.api.audio.stream_audio_content') as mock_stream:
            async def fake_stream():
                yield b"audio data"
            
            mock_stream.return_value = fake_stream()
            
            # Test full file request
            response = client.get("/api/v1/digests/test-digest/audio")
            assert response.status_code == 200
            assert response.headers["Accept-Ranges"] == "bytes"
            assert response.headers["Content-Type"] == "audio/mpeg"
            
            # Test range request
            response = client.get(
                "/api/v1/digests/test-digest/audio",
                headers={"Range": "bytes=1000-"}
            )
            assert response.status_code == 206
            assert "Content-Range" in response.headers


@pytest.mark.asyncio
async def test_audio_cleanup():
    """Test old audio file cleanup."""
    mock_supabase = Mock()
    
    # Mock list_audio_files response
    old_file = {"name": f"digest-123-{int(1000000000)}.mp3"}  # Old timestamp
    new_file = {"name": f"digest-456-{int(9999999999)}.mp3"}  # Future timestamp
    
    service = AudioStorageService(mock_supabase)
    
    with patch.object(service, 'list_audio_files', return_value=[old_file, new_file]):
        with patch.object(service, 'delete_audio', return_value=True) as mock_delete:
            deleted = await service.cleanup_old_files(days=30)
            assert deleted == 1
            mock_delete.assert_called_once_with(old_file['name'])