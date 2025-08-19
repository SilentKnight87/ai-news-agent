"""
Scheduled task service for automated article fetching and digest generation.

This module provides background scheduling capabilities for regular
news fetching and daily digest generation using asyncio.
"""

import asyncio
import logging
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any

from ..config import get_settings

logger = logging.getLogger(__name__)


class ScheduledTask:
    """
    Represents a scheduled task with timing and execution details.
    """

    def __init__(
        self,
        name: str,
        func: Callable,
        interval_minutes: int | None = None,
        daily_at_hour: int | None = None,
        args: tuple = (),
        kwargs: dict[str, Any] | None = None
    ):
        """
        Initialize a scheduled task.
        
        Args:
            name: Task name for identification.
            func: Async function to execute.
            interval_minutes: Run every N minutes (for periodic tasks).
            daily_at_hour: Run daily at specific hour UTC (for daily tasks).
            args: Arguments to pass to the function.
            kwargs: Keyword arguments to pass to the function.
        """
        self.name = name
        self.func = func
        self.interval_minutes = interval_minutes
        self.daily_at_hour = daily_at_hour
        self.args = args
        self.kwargs = kwargs or {}

        self.last_run: datetime | None = None
        self.next_run: datetime | None = None
        self.run_count = 0
        self.error_count = 0
        self.is_running = False

        # Validate task configuration
        if interval_minutes is None and daily_at_hour is None:
            raise ValueError("Must specify either interval_minutes or daily_at_hour")
        if interval_minutes is not None and daily_at_hour is not None:
            raise ValueError("Cannot specify both interval_minutes and daily_at_hour")
        if daily_at_hour is not None and (daily_at_hour < 0 or daily_at_hour > 23):
            raise ValueError("daily_at_hour must be between 0 and 23")

        self._calculate_next_run()

        logger.debug(f"Created scheduled task '{name}' - next run: {self.next_run}")

    def _calculate_next_run(self) -> None:
        """Calculate the next run time for this task."""
        now = datetime.now(UTC)

        if self.interval_minutes is not None:
            # Periodic task
            if self.last_run is None:
                self.next_run = now + timedelta(seconds=10)  # Start soon for first run
            else:
                self.next_run = self.last_run + timedelta(minutes=self.interval_minutes)

        elif self.daily_at_hour is not None:
            # Daily task
            today = now.replace(hour=self.daily_at_hour, minute=0, second=0, microsecond=0)

            if now > today:
                # Next run is tomorrow
                self.next_run = today + timedelta(days=1)
            else:
                # Next run is today
                self.next_run = today

    def should_run(self, current_time: datetime) -> bool:
        """
        Check if this task should run now.
        
        Args:
            current_time: Current time to check against.
            
        Returns:
            bool: True if task should run.
        """
        if self.is_running:
            return False

        return self.next_run is not None and current_time >= self.next_run

    async def execute(self) -> bool:
        """
        Execute the scheduled task.
        
        Returns:
            bool: True if execution was successful.
        """
        if self.is_running:
            logger.warning(f"Task '{self.name}' is already running, skipping")
            return False

        self.is_running = True
        start_time = datetime.now(UTC)

        try:
            logger.info(f"Executing scheduled task: {self.name}")

            # Execute the task function
            if asyncio.iscoroutinefunction(self.func):
                await self.func(*self.args, **self.kwargs)
            else:
                self.func(*self.args, **self.kwargs)

            # Update task state
            self.last_run = start_time
            self.run_count += 1
            self._calculate_next_run()

            execution_time = (datetime.now(UTC) - start_time).total_seconds()
            logger.info(
                f"Task '{self.name}' completed successfully in {execution_time:.2f}s "
                f"(next run: {self.next_run})"
            )

            return True

        except Exception as e:
            self.error_count += 1
            execution_time = (datetime.now(UTC) - start_time).total_seconds()

            logger.error(
                f"Task '{self.name}' failed after {execution_time:.2f}s: {e}",
                exc_info=True
            )

            # Still update last run time and calculate next run
            self.last_run = start_time
            self._calculate_next_run()

            return False

        finally:
            self.is_running = False

    def get_status(self) -> dict[str, Any]:
        """
        Get current status of the task.
        
        Returns:
            Dict: Task status information.
        """
        return {
            "name": self.name,
            "is_running": self.is_running,
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "next_run": self.next_run.isoformat() if self.next_run else None,
            "run_count": self.run_count,
            "error_count": self.error_count,
            "success_rate": (
                (self.run_count - self.error_count) / self.run_count * 100
                if self.run_count > 0 else 0
            )
        }


class TaskScheduler:
    """
    Background task scheduler for automated operations.
    
    Manages periodic and daily scheduled tasks with error handling
    and status monitoring.
    """

    def __init__(self):
        """Initialize the task scheduler."""
        self.tasks: list[ScheduledTask] = []
        self.is_running = False
        self._scheduler_task: asyncio.Task | None = None
        self.settings = get_settings()

        logger.info("Task scheduler initialized")

    def add_task(
        self,
        name: str,
        func: Callable,
        interval_minutes: int | None = None,
        daily_at_hour: int | None = None,
        args: tuple = (),
        kwargs: dict[str, Any] | None = None
    ) -> ScheduledTask:
        """
        Add a new scheduled task.
        
        Args:
            name: Task name for identification.
            func: Async function to execute.
            interval_minutes: Run every N minutes (for periodic tasks).
            daily_at_hour: Run daily at specific hour UTC (for daily tasks).
            args: Arguments to pass to the function.
            kwargs: Keyword arguments to pass to the function.
            
        Returns:
            ScheduledTask: The created task.
        """
        # Check for duplicate task names
        if any(task.name == name for task in self.tasks):
            raise ValueError(f"Task with name '{name}' already exists")

        task = ScheduledTask(
            name=name,
            func=func,
            interval_minutes=interval_minutes,
            daily_at_hour=daily_at_hour,
            args=args,
            kwargs=kwargs
        )

        self.tasks.append(task)
        logger.info(f"Added scheduled task: {name}")

        return task

    def remove_task(self, name: str) -> bool:
        """
        Remove a scheduled task by name.
        
        Args:
            name: Task name to remove.
            
        Returns:
            bool: True if task was found and removed.
        """
        for i, task in enumerate(self.tasks):
            if task.name == name:
                del self.tasks[i]
                logger.info(f"Removed scheduled task: {name}")
                return True

        logger.warning(f"Task '{name}' not found for removal")
        return False

    def get_task(self, name: str) -> ScheduledTask | None:
        """
        Get a task by name.
        
        Args:
            name: Task name to find.
            
        Returns:
            Optional[ScheduledTask]: Task if found, None otherwise.
        """
        for task in self.tasks:
            if task.name == name:
                return task
        return None

    async def start(self) -> None:
        """Start the task scheduler."""
        if self.is_running:
            logger.warning("Task scheduler is already running")
            return

        self.is_running = True
        logger.info("Starting task scheduler")

        # Start the scheduler loop
        self._scheduler_task = asyncio.create_task(self._scheduler_loop())

    async def stop(self) -> None:
        """Stop the task scheduler."""
        if not self.is_running:
            return

        logger.info("Stopping task scheduler")
        self.is_running = False

        if self._scheduler_task:
            self._scheduler_task.cancel()
            try:
                await self._scheduler_task
            except asyncio.CancelledError:
                pass
            self._scheduler_task = None

    async def _scheduler_loop(self) -> None:
        """Main scheduler loop that checks and executes tasks."""
        check_interval = 30  # Check every 30 seconds

        try:
            while self.is_running:
                current_time = datetime.now(UTC)

                # Check all tasks for execution
                tasks_to_run = [
                    task for task in self.tasks
                    if task.should_run(current_time)
                ]

                # Execute tasks concurrently
                if tasks_to_run:
                    logger.debug(f"Executing {len(tasks_to_run)} scheduled tasks")

                    # Create tasks for concurrent execution
                    execution_tasks = [
                        asyncio.create_task(task.execute())
                        for task in tasks_to_run
                    ]

                    # Wait for all tasks to complete
                    await asyncio.gather(*execution_tasks, return_exceptions=True)

                # Wait before next check
                await asyncio.sleep(check_interval)

        except asyncio.CancelledError:
            logger.info("Scheduler loop cancelled")
            raise
        except Exception as e:
            logger.error(f"Scheduler loop error: {e}", exc_info=True)
            raise

    def get_status(self) -> dict[str, Any]:
        """
        Get current status of the scheduler and all tasks.
        
        Returns:
            Dict: Scheduler status information.
        """
        return {
            "is_running": self.is_running,
            "total_tasks": len(self.tasks),
            "tasks": [task.get_status() for task in self.tasks],
            "next_task_run": min(
                (task.next_run for task in self.tasks if task.next_run),
                default=None
            )
        }

    async def run_task_now(self, name: str) -> bool:
        """
        Manually trigger a task to run immediately.
        
        Args:
            name: Task name to execute.
            
        Returns:
            bool: True if task was found and executed successfully.
        """
        task = self.get_task(name)
        if not task:
            logger.error(f"Task '{name}' not found")
            return False

        logger.info(f"Manually triggering task: {name}")
        return await task.execute()


# Global scheduler instance
_scheduler: TaskScheduler | None = None


def get_scheduler() -> TaskScheduler:
    """
    Get the global task scheduler instance.
    
    Returns:
        TaskScheduler: Global scheduler.
    """
    global _scheduler
    if _scheduler is None:
        _scheduler = TaskScheduler()
    return _scheduler


async def setup_default_tasks() -> None:
    """
    Set up default scheduled tasks for the AI news aggregator.
    """
    from dotenv import load_dotenv
    
    # Load environment variables from .env file
    load_dotenv()
    
    from ..api.dependencies import (
        get_article_repository,
        get_deduplication_service,
        get_news_analyzer,
        get_supabase_client,
    )
    from ..api.routes import fetch_articles_background
    from ..models.articles import ArticleSource

    scheduler = get_scheduler()
    settings = get_settings()

    # Set up dependencies for background tasks
    supabase = get_supabase_client()
    article_repo = get_article_repository(supabase)
    deduplication_service = get_deduplication_service(supabase)
    news_analyzer = get_news_analyzer()

    # Task 1: Periodic article fetching
    async def fetch_all_sources():
        """Fetch articles from all sources."""
        try:
            sources = list(ArticleSource)
            await fetch_articles_background(
                sources,
                article_repo,
                deduplication_service,
                news_analyzer
            )
        except Exception as e:
            logger.error(f"Scheduled fetch failed: {e}")
            raise

    scheduler.add_task(
        name="fetch_articles",
        func=fetch_all_sources,
        interval_minutes=settings.fetch_interval_minutes
    )

    # Task 2: Daily digest generation
    async def generate_daily_digest():
        """Generate daily digest and queue audio generation."""
        try:
            from ..agents.digest_agent import get_digest_agent
            from ..services.audio_queue import get_audio_queue

            # Get articles from last 24 hours
            articles = await article_repo.get_top_articles_for_digest(
                since_hours=24,
                min_relevance_score=50.0,
                limit=20
            )

            if not articles:
                logger.warning("No articles found for daily digest")
                return

            # Generate digest
            digest_agent = get_digest_agent()
            digest_date = datetime.now(UTC)
            digest = await digest_agent.generate_digest(articles, digest_date)

            # Save digest to database (this would be done in the repository)
            # For now, let's assume digest has an ID after saving

            # Queue audio generation if TTS is configured
            if settings.elevenlabs_api_key and hasattr(digest, 'id'):
                try:
                    audio_queue = get_audio_queue()
                    await audio_queue.queue_audio_generation(
                        digest_id=str(digest.id),
                        text=digest.summary_text,
                        voice_type="news"
                    )
                    logger.info(f"Queued audio generation for digest: {digest.id}")
                except Exception as e:
                    logger.warning(f"Failed to queue audio generation: {e}")

            logger.info(f"Generated daily digest with {len(digest.top_articles)} articles")

        except Exception as e:
            logger.error(f"Digest generation failed: {e}")
            raise

    scheduler.add_task(
        name="daily_digest",
        func=generate_daily_digest,
        daily_at_hour=settings.digest_hour_utc
    )

    # Task 3: Process audio queue (every minute)
    from ..tasks.audio_tasks import process_audio_queue

    scheduler.add_task(
        name="process_audio_queue",
        func=process_audio_queue,
        interval_minutes=1
    )

    # Task 4: Clean up old audio files (daily)
    from ..tasks.audio_tasks import cleanup_old_audio

    scheduler.add_task(
        name="cleanup_audio",
        func=cleanup_old_audio,
        daily_at_hour=3  # Run at 3 AM UTC
    )

    # Task 5: Retry failed audio tasks (hourly)
    from ..tasks.audio_tasks import retry_failed_audio

    scheduler.add_task(
        name="retry_failed_audio",
        func=retry_failed_audio,
        interval_minutes=60
    )

    logger.info("Default scheduled tasks configured with audio processing")


async def start_scheduler() -> None:
    """Start the task scheduler with default tasks."""
    scheduler = get_scheduler()

    # Set up default tasks
    await setup_default_tasks()

    # Start the scheduler
    await scheduler.start()

    logger.info("Task scheduler started with default tasks")


async def stop_scheduler() -> None:
    """Stop the task scheduler."""
    scheduler = get_scheduler()
    await scheduler.stop()
    logger.info("Task scheduler stopped")
