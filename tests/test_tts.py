"""
Tests for TTS service.
"""

import asyncio
import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

from src.services.tts import (
    TTSConfig,
    TTSResult,
    TTSService,
    get_tts_service,
    generate_digest_audio
)


class TestTTSConfig:
    """Test the TTSConfig model."""
    
    def test_default_config(self):
        """Test default TTS configuration."""
        config = TTSConfig()
        
        assert config.voice_id == "21m00Tcm4TlvDq8ikWAM"
        assert config.model_id == "eleven_monolingual_v1"
        assert config.stability == 0.5
        assert config.similarity_boost == 0.5
        assert config.style == 0.0
        assert config.use_speaker_boost is True
    
    def test_custom_config(self):
        """Test custom TTS configuration."""
        config = TTSConfig(
            voice_id="custom_voice",
            stability=0.8,
            similarity_boost=0.7,
            style=0.2
        )
        
        assert config.voice_id == "custom_voice"
        assert config.stability == 0.8
        assert config.similarity_boost == 0.7
        assert config.style == 0.2


class TestTTSResult:
    """Test the TTSResult model."""
    
    def test_tts_result_creation(self):
        """Test TTS result model creation."""
        result = TTSResult(
            text_hash="abc123",
            audio_file_path="/path/to/audio.mp3",
            file_size_bytes=1024,
            generation_time_seconds=2.5
        )
        
        assert result.text_hash == "abc123"
        assert result.audio_file_path == "/path/to/audio.mp3"
        assert result.file_size_bytes == 1024
        assert result.generation_time_seconds == 2.5
        assert result.duration_seconds is None


class TestTTSService:
    """Test the TTSService class."""
    
    @pytest.fixture
    def temp_output_dir(self):
        """Create a temporary output directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir
    
    @patch('src.services.tts.get_settings')
    def test_tts_service_initialization(self, mock_get_settings, temp_output_dir):
        """Test TTS service initialization."""
        mock_settings = Mock()
        mock_settings.elevenlabs_api_key = "test_api_key"
        mock_settings.max_digest_chars = 2000
        mock_get_settings.return_value = mock_settings
        
        service = TTSService(output_dir=temp_output_dir)
        
        assert service.output_dir == Path(temp_output_dir)
        assert service.output_dir.exists()
        assert service.headers["xi-api-key"] == "test_api_key"
    
    def test_generate_text_hash(self, temp_output_dir):
        """Test text hash generation."""
        with patch('src.services.tts.get_settings') as mock_get_settings:
            mock_settings = Mock()
            mock_settings.elevenlabs_api_key = "test_key"
            mock_get_settings.return_value = mock_settings
            
            service = TTSService(output_dir=temp_output_dir)
            
            hash1 = service._generate_text_hash("Hello world")
            hash2 = service._generate_text_hash("Hello world")
            hash3 = service._generate_text_hash("Different text")
            
            assert hash1 == hash2  # Same text should have same hash
            assert hash1 != hash3  # Different text should have different hash
            assert len(hash1) == 16  # Hash should be 16 characters
    
    def test_get_cache_path(self, temp_output_dir):
        """Test cache path generation."""
        with patch('src.services.tts.get_settings') as mock_get_settings:
            mock_settings = Mock()
            mock_settings.elevenlabs_api_key = "test_key"
            mock_get_settings.return_value = mock_settings
            
            service = TTSService(output_dir=temp_output_dir)
            cache_path = service._get_cache_path("abc123")
            
            expected_path = Path(temp_output_dir) / "tts_abc123.mp3"
            assert cache_path == expected_path
    
    @pytest.mark.asyncio
    async def test_is_cached(self, temp_output_dir):
        """Test cache checking."""
        with patch('src.services.tts.get_settings') as mock_get_settings:
            mock_settings = Mock()
            mock_settings.elevenlabs_api_key = "test_key"
            mock_get_settings.return_value = mock_settings
            
            service = TTSService(output_dir=temp_output_dir)
            
            # Should not be cached initially
            assert await service.is_cached("test text") is False
            
            # Create a cache file
            text_hash = service._generate_text_hash("test text")
            cache_path = service._get_cache_path(text_hash)
            cache_path.write_bytes(b"fake audio data")
            
            # Should now be cached
            assert await service.is_cached("test text") is True
    
    @pytest.mark.asyncio
    async def test_get_cached_result(self, temp_output_dir):
        """Test retrieving cached results."""
        with patch('src.services.tts.get_settings') as mock_get_settings:
            mock_settings = Mock()
            mock_settings.elevenlabs_api_key = "test_key"
            mock_get_settings.return_value = mock_settings
            
            service = TTSService(output_dir=temp_output_dir)
            
            # Should return None for non-cached text
            result = await service.get_cached_result("not cached")
            assert result is None
            
            # Create a cache file
            text_hash = service._generate_text_hash("cached text")
            cache_path = service._get_cache_path(text_hash)
            test_data = b"fake audio data"
            cache_path.write_bytes(test_data)
            
            # Should return cached result
            result = await service.get_cached_result("cached text")
            assert result is not None
            assert result.text_hash == text_hash
            assert result.file_size_bytes == len(test_data)
            assert result.generation_time_seconds == 0.0
    
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_generate_speech_success(self, mock_client_class, temp_output_dir):
        """Test successful speech generation."""
        with patch('src.services.tts.get_settings') as mock_get_settings:
            mock_settings = Mock()
            mock_settings.elevenlabs_api_key = "test_key"
            mock_settings.max_digest_chars = 2000
            mock_get_settings.return_value = mock_settings
            
            # Mock HTTP response
            mock_response = Mock()
            mock_response.content = b"fake audio content"
            mock_response.raise_for_status = Mock()
            
            mock_client = Mock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client
            
            service = TTSService(output_dir=temp_output_dir)
            
            result = await service.generate_speech("Test text", use_cache=False)
            
            assert result.text_hash == service._generate_text_hash("Test text")
            assert result.file_size_bytes == len(b"fake audio content")
            assert result.generation_time_seconds > 0
            
            # Check that file was created
            cache_path = Path(result.audio_file_path)
            assert cache_path.exists()
            assert cache_path.read_bytes() == b"fake audio content"
    
    @pytest.mark.asyncio
    async def test_generate_speech_no_api_key(self, temp_output_dir):
        """Test speech generation without API key."""
        with patch('src.services.tts.get_settings') as mock_get_settings:
            mock_settings = Mock()
            mock_settings.elevenlabs_api_key = None
            mock_get_settings.return_value = mock_settings
            
            service = TTSService(output_dir=temp_output_dir)
            
            with pytest.raises(ValueError, match="ElevenLabs API key not configured"):
                await service.generate_speech("Test text")
    
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_generate_speech_api_error(self, mock_client_class, temp_output_dir):
        """Test speech generation with API error."""
        with patch('src.services.tts.get_settings') as mock_get_settings:
            mock_settings = Mock()
            mock_settings.elevenlabs_api_key = "test_key"
            mock_get_settings.return_value = mock_settings
            
            # Mock HTTP error
            mock_response = Mock()
            mock_response.status_code = 401
            mock_response.text = "Unauthorized"
            
            from httpx import HTTPStatusError
            mock_client = Mock()
            mock_client.post = AsyncMock(side_effect=HTTPStatusError(
                "Unauthorized", request=Mock(), response=mock_response
            ))
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client
            
            service = TTSService(output_dir=temp_output_dir)
            
            with pytest.raises(Exception, match="TTS generation failed: 401"):
                await service.generate_speech("Test text", use_cache=False)
    
    @pytest.mark.asyncio
    async def test_generate_digest_audio(self, temp_output_dir):
        """Test digest audio generation with text enhancement."""
        with patch('src.services.tts.get_settings') as mock_get_settings:
            mock_settings = Mock()
            mock_settings.elevenlabs_api_key = "test_key"
            mock_settings.max_digest_chars = 100  # Small limit for testing
            mock_get_settings.return_value = mock_settings
            
            service = TTSService(output_dir=temp_output_dir)
            
            # Mock the generate_speech method
            service.generate_speech = AsyncMock(return_value=TTSResult(
                text_hash="digest_hash",
                audio_file_path="/fake/path.mp3",
                file_size_bytes=1024,
                generation_time_seconds=2.0
            ))
            
            long_text = "A" * 200  # Text longer than max_digest_chars
            result = await service.generate_digest_audio(long_text)
            
            # Should have called generate_speech with enhanced text
            service.generate_speech.assert_called_once()
            call_args = service.generate_speech.call_args[0][0]
            
            assert "Good morning" in call_args
            assert "Stay curious" in call_args
            assert len(call_args) < len(long_text) + 200  # Should be truncated
    
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_list_available_voices(self, mock_client_class, temp_output_dir):
        """Test listing available voices."""
        with patch('src.services.tts.get_settings') as mock_get_settings:
            mock_settings = Mock()
            mock_settings.elevenlabs_api_key = "test_key"
            mock_get_settings.return_value = mock_settings
            
            # Mock API response
            mock_response = Mock()
            mock_response.json.return_value = {
                "voices": [
                    {"voice_id": "voice1", "name": "Voice 1"},
                    {"voice_id": "voice2", "name": "Voice 2"}
                ]
            }
            mock_response.raise_for_status = Mock()
            
            mock_client = Mock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client
            
            service = TTSService(output_dir=temp_output_dir)
            voices = await service.list_available_voices()
            
            assert len(voices) == 2
            assert voices[0]["voice_id"] == "voice1"
            assert voices[1]["name"] == "Voice 2"
    
    def test_get_cache_stats(self, temp_output_dir):
        """Test cache statistics."""
        with patch('src.services.tts.get_settings') as mock_get_settings:
            mock_settings = Mock()
            mock_settings.elevenlabs_api_key = "test_key"
            mock_get_settings.return_value = mock_settings
            
            service = TTSService(output_dir=temp_output_dir)
            
            # Empty cache
            stats = service.get_cache_stats()
            assert stats["total_files"] == 0
            assert stats["total_size_bytes"] == 0
            
            # Add some cache files
            (Path(temp_output_dir) / "tts_hash1.mp3").write_bytes(b"audio1")  # 6 bytes
            (Path(temp_output_dir) / "tts_hash2.mp3").write_bytes(b"audio22")  # 7 bytes
            
            stats = service.get_cache_stats()
            assert stats["total_files"] == 2
            assert stats["total_size_bytes"] == 13  # 6 + 7 bytes
            assert stats["total_size_mb"] == 0.0
    
    @pytest.mark.asyncio
    async def test_cleanup_old_cache(self, temp_output_dir):
        """Test cache cleanup."""
        with patch('src.services.tts.get_settings') as mock_get_settings:
            mock_settings = Mock()
            mock_settings.elevenlabs_api_key = "test_key"
            mock_get_settings.return_value = mock_settings
            
            service = TTSService(output_dir=temp_output_dir)
            
            # Create multiple cache files
            for i in range(5):
                cache_file = Path(temp_output_dir) / f"tts_hash{i}.mp3"
                cache_file.write_bytes(b"audio data")
                # Simulate different modification times
                await asyncio.sleep(0.01)
            
            # Cleanup, keeping only 2 latest
            deleted_count = await service.cleanup_old_cache(keep_latest=2)
            
            assert deleted_count == 3
            
            # Check remaining files
            remaining_files = list(Path(temp_output_dir).glob("tts_*.mp3"))
            assert len(remaining_files) == 2


class TestGlobalTTSService:
    """Test the global TTS service functionality."""
    
    def test_get_tts_service_singleton(self):
        """Test that get_tts_service returns singleton."""
        service1 = get_tts_service()
        service2 = get_tts_service()
        
        assert service1 is service2
        assert isinstance(service1, TTSService)


@pytest.mark.asyncio
async def test_generate_digest_audio_convenience_function():
    """Test the convenience function for generating digest audio."""
    
    with patch('src.services.tts.get_tts_service') as mock_get_service:
        mock_service = Mock()
        mock_service.generate_digest_audio = AsyncMock(return_value=TTSResult(
            text_hash="test_hash",
            audio_file_path="/test/path.mp3",
            file_size_bytes=1024,
            generation_time_seconds=1.5
        ))
        mock_get_service.return_value = mock_service
        
        result = await generate_digest_audio("Test digest text")
        
        assert result.text_hash == "test_hash"
        assert result.file_size_bytes == 1024
        mock_service.generate_digest_audio.assert_called_once_with("Test digest text")