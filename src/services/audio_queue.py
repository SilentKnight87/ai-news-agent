"""
Audio queue processor for background TTS generation.

This module manages the audio generation queue, processing tasks
asynchronously with retry logic and error handling.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from pathlib import Path

from ..models.audio import AudioGenerationTask, AudioStatus
from .audio_storage import get_audio_storage_service
from .tts import get_tts_service

logger = logging.getLogger(__name__)


class AudioQueueService:
    """Manages audio generation queue and processing."""

    def __init__(self):
        """Initialize audio queue service."""
        self.tts_service = get_tts_service()
        self.processing_lock = asyncio.Lock()
        self.queue: list[AudioGenerationTask] = []
        self.max_retries = 3
        self.retry_delay = 60  # seconds

        logger.info("Audio queue service initialized")

    async def queue_audio_generation(
        self,
        digest_id: str,
        text: str | None = None,
        voice_type: str = "news",
        force: bool = False
    ) -> bool:
        """
        Queue audio generation for a digest.
        
        Args:
            digest_id: ID of the digest.
            text: Text to convert (fetches from digest if None).
            voice_type: Voice type to use.
            force: Force regeneration even if exists.
            
        Returns:
            bool: True if queued successfully.
        """
        try:
            # Fetch text from digest if not provided
            if text is None:
                from ..api.dependencies import get_supabase_client
                supabase = get_supabase_client()

                # Query digest directly
                result = supabase.table("daily_digests").select("*").eq("id", digest_id).single().execute()
                digest = result.data

                if not digest:
                    logger.error(f"Digest not found: {digest_id}")
                    return False

                text = digest["summary_text"]

            # Check if already in queue
            if not force:
                for task in self.queue:
                    if task.digest_id == digest_id and task.status != AudioStatus.FAILED:
                        logger.info(f"Audio already in queue for digest: {digest_id}")
                        return True

            # Create task
            task = AudioGenerationTask(
                digest_id=digest_id,
                text=text,
                voice_type=voice_type
            )

            self.queue.append(task)
            logger.info(f"Queued audio generation for digest: {digest_id}")

            return True

        except Exception as e:
            logger.error(f"Failed to queue audio generation: {e}")
            return False

    async def process_queue(self) -> int:
        """
        Process pending audio generation tasks.
        
        Returns:
            int: Number of tasks processed.
        """
        async with self.processing_lock:
            processed_count = 0

            # Get pending tasks
            pending_tasks = [
                task for task in self.queue
                if task.status == AudioStatus.PENDING
            ]

            for task in pending_tasks:
                try:
                    await self._process_task(task)
                    processed_count += 1

                except Exception as e:
                    logger.error(f"Failed to process audio task: {e}")
                    task.status = AudioStatus.FAILED
                    task.error_message = str(e)

            # Clean up completed tasks older than 1 hour
            cutoff_time = datetime.utcnow() - timedelta(hours=1)
            self.queue = [
                task for task in self.queue
                if task.status != AudioStatus.COMPLETED or task.processed_at > cutoff_time
            ]

            if processed_count > 0:
                logger.info(f"Processed {processed_count} audio generation tasks")

            return processed_count

    async def _process_task(self, task: AudioGenerationTask):
        """
        Process a single audio generation task.
        
        Args:
            task: Task to process.
        """
        task.status = AudioStatus.PROCESSING
        retry_count = 0

        while retry_count < self.max_retries:
            try:
                logger.info(f"Generating audio for digest: {task.digest_id}")

                # Generate audio
                tts_result = await self.tts_service.generate_digest_audio(task.text, voice_type=task.voice_type)

                # Upload to storage
                from ..api.dependencies import get_supabase_client
                supabase = get_supabase_client()
                storage_service = get_audio_storage_service(supabase)

                audio_url = await storage_service.upload_audio(
                    digest_id=task.digest_id,
                    audio_path=Path(tts_result.audio_file_path),
                    metadata={
                        "voice_type": task.voice_type,
                        "duration": tts_result.duration_seconds,
                        "size": tts_result.file_size_bytes
                    }
                )

                # Update digest with audio URL
                supabase.table("daily_digests").update({"audio_url": audio_url}).eq("id", task.digest_id).execute()

                # Mark as completed
                task.status = AudioStatus.COMPLETED
                task.processed_at = datetime.utcnow()

                logger.info(f"Audio generated successfully for digest: {task.digest_id}")
                return

            except Exception as e:
                retry_count += 1
                logger.warning(f"Audio generation attempt {retry_count} failed: {e}")

                if retry_count < self.max_retries:
                    await asyncio.sleep(self.retry_delay)
                else:
                    task.status = AudioStatus.FAILED
                    task.error_message = str(e)
                    raise

    async def get_queue_status(self) -> dict:
        """
        Get current queue status.
        
        Returns:
            dict: Queue statistics.
        """
        status_counts = {
            AudioStatus.PENDING: 0,
            AudioStatus.PROCESSING: 0,
            AudioStatus.COMPLETED: 0,
            AudioStatus.FAILED: 0
        }

        for task in self.queue:
            status_counts[task.status] += 1

        return {
            "total_tasks": len(self.queue),
            "pending": status_counts[AudioStatus.PENDING],
            "processing": status_counts[AudioStatus.PROCESSING],
            "completed": status_counts[AudioStatus.COMPLETED],
            "failed": status_counts[AudioStatus.FAILED]
        }

    async def retry_failed_tasks(self) -> int:
        """
        Retry failed tasks.
        
        Returns:
            int: Number of tasks retried.
        """
        failed_tasks = [
            task for task in self.queue
            if task.status == AudioStatus.FAILED
        ]

        for task in failed_tasks:
            task.status = AudioStatus.PENDING
            task.error_message = None

        logger.info(f"Retrying {len(failed_tasks)} failed audio tasks")
        return len(failed_tasks)


# Global instance
_audio_queue_service: AudioQueueService | None = None


def get_audio_queue() -> AudioQueueService:
    """
    Get the global audio queue service.
    
    Returns:
        AudioQueueService: Global service instance.
    """
    global _audio_queue_service
    if _audio_queue_service is None:
        _audio_queue_service = AudioQueueService()
    return _audio_queue_service
