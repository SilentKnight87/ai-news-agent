"""
Background audio tasks for scheduled processing.

This module contains background tasks for audio generation,
cleanup, and queue processing.
"""

import logging
from datetime import datetime

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from ..api.dependencies import get_supabase_client
from ..services.audio_queue import get_audio_queue
from ..services.audio_storage import get_audio_storage_service

logger = logging.getLogger(__name__)


async def process_audio_queue():
    """
    Process pending audio generation tasks.
    
    This task runs every minute to process any pending
    audio generation requests in the queue.
    """
    try:
        logger.debug("Processing audio queue")
        audio_queue = get_audio_queue()
        processed = await audio_queue.process_queue()

        if processed > 0:
            logger.info(f"Processed {processed} audio generation tasks")

    except Exception as e:
        logger.error(f"Error processing audio queue: {e}")


async def cleanup_old_audio():
    """
    Clean up old audio files from storage.
    
    This task runs daily to remove audio files older than
    the configured retention period (default 30 days).
    """
    try:
        logger.info("Starting audio cleanup task")

        supabase = get_supabase_client()
        storage_service = get_audio_storage_service(supabase)

        # Clean up files older than 30 days
        deleted = await storage_service.cleanup_old_files(days=30)

        if deleted > 0:
            logger.info(f"Cleaned up {deleted} old audio files")
        else:
            logger.debug("No old audio files to clean up")

    except Exception as e:
        logger.error(f"Error during audio cleanup: {e}")


async def retry_failed_audio():
    """
    Retry failed audio generation tasks.
    
    This task runs every hour to retry any failed
    audio generation tasks.
    """
    try:
        logger.debug("Checking for failed audio tasks")
        audio_queue = get_audio_queue()
        retried = await audio_queue.retry_failed_tasks()

        if retried > 0:
            logger.info(f"Retrying {retried} failed audio tasks")

    except Exception as e:
        logger.error(f"Error retrying failed audio tasks: {e}")


async def generate_missing_audio():
    """
    Generate audio for digests that are missing audio.
    
    This task runs daily to ensure all recent digests
    have audio generated.
    """
    try:
        logger.info("Checking for digests missing audio")

        supabase = get_supabase_client()
        audio_queue = get_audio_queue()

        # Query digests without audio from last 7 days
        from datetime import timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=7)

        result = supabase.table("daily_digests") \
            .select("id, summary_text") \
            .is_("audio_url", "null") \
            .gte("created_at", cutoff_date.isoformat()) \
            .execute()

        if result.data:
            logger.info(f"Found {len(result.data)} digests missing audio")

            for digest in result.data:
                await audio_queue.queue_audio_generation(
                    digest_id=digest["id"],
                    text=digest["summary_text"]
                )
        else:
            logger.debug("All recent digests have audio")

    except Exception as e:
        logger.error(f"Error generating missing audio: {e}")


async def monitor_audio_queue():
    """
    Monitor and log audio queue status.
    
    This task runs every 5 minutes to log the current
    status of the audio generation queue.
    """
    try:
        audio_queue = get_audio_queue()
        status = await audio_queue.get_queue_status()

        if status["total_tasks"] > 0:
            logger.info(
                f"Audio queue status - Total: {status['total_tasks']}, "
                f"Pending: {status['pending']}, Processing: {status['processing']}, "
                f"Completed: {status['completed']}, Failed: {status['failed']}"
            )

    except Exception as e:
        logger.error(f"Error monitoring audio queue: {e}")
