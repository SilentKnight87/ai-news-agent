"""
Supabase Storage service for audio files.

This module manages audio file storage in Supabase Storage,
providing upload, retrieval, and cleanup capabilities.
"""

import logging
import time
from pathlib import Path

from supabase import Client

logger = logging.getLogger(__name__)


class AudioStorageService:
    """Manages audio file storage in Supabase."""

    BUCKET_NAME = "audio-digests"

    def __init__(self, supabase_client: Client):
        """
        Initialize audio storage service.
        
        Args:
            supabase_client: Supabase client instance.
        """
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
                logger.info(f"Created storage bucket: {self.BUCKET_NAME}")
        except Exception as e:
            logger.error(f"Failed to ensure bucket: {e}")

    async def upload_audio(
        self,
        digest_id: str,
        audio_path: Path,
        metadata: dict | None = None
    ) -> str:
        """
        Upload audio file to Supabase Storage.
        
        Args:
            digest_id: ID of the digest.
            audio_path: Path to audio file.
            metadata: Optional metadata.
            
        Returns:
            str: Public URL of uploaded file.
            
        Raises:
            Exception: If upload fails.
        """
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

    async def get_audio_url(self, filename: str) -> str:
        """
        Get public URL for an audio file.
        
        Args:
            filename: Name of the file in storage.
            
        Returns:
            str: Public URL.
        """
        return self.supabase.storage.from_(self.BUCKET_NAME).get_public_url(filename)

    async def delete_audio(self, filename: str) -> bool:
        """
        Delete an audio file from storage.
        
        Args:
            filename: Name of the file to delete.
            
        Returns:
            bool: True if deleted successfully.
        """
        try:
            self.supabase.storage.from_(self.BUCKET_NAME).remove([filename])
            logger.info(f"Deleted audio file: {filename}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete audio: {e}")
            return False

    async def list_audio_files(self, prefix: str | None = None) -> list[dict]:
        """
        List audio files in the bucket.
        
        Args:
            prefix: Optional prefix to filter files.
            
        Returns:
            list[dict]: List of file metadata.
        """
        try:
            files = self.supabase.storage.from_(self.BUCKET_NAME).list(prefix=prefix)
            return files
        except Exception as e:
            logger.error(f"Failed to list audio files: {e}")
            return []

    async def cleanup_old_files(self, days: int = 30) -> int:
        """
        Delete audio files older than specified days.
        
        Args:
            days: Age threshold in days.
            
        Returns:
            int: Number of files deleted.
        """
        try:
            files = await self.list_audio_files()
            current_time = time.time()
            deleted_count = 0

            for file in files:
                # Parse file timestamp from filename
                # Format: digest-{id}-{timestamp}.mp3
                try:
                    parts = file['name'].split('-')
                    if len(parts) >= 3:
                        file_timestamp = int(parts[-1].replace('.mp3', ''))
                        age_days = (current_time - file_timestamp) / 86400

                        if age_days > days:
                            if await self.delete_audio(file['name']):
                                deleted_count += 1

                except (ValueError, IndexError):
                    continue

            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} old audio files")

            return deleted_count

        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
            return 0


# Global instance
_audio_storage_service: AudioStorageService | None = None


def get_audio_storage_service(supabase_client: Client) -> AudioStorageService:
    """
    Get the global audio storage service instance.
    
    Args:
        supabase_client: Supabase client.
        
    Returns:
        AudioStorageService: Global service instance.
    """
    global _audio_storage_service
    if _audio_storage_service is None:
        _audio_storage_service = AudioStorageService(supabase_client)
    return _audio_storage_service
