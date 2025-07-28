"""
Tests for task scheduler service.
"""

import asyncio
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, AsyncMock

from src.services.scheduler import (
    ScheduledTask,
    TaskScheduler,
    get_scheduler
)


class TestScheduledTask:
    """Test the ScheduledTask class."""
    
    def test_periodic_task_creation(self):
        """Test creating a periodic task."""
        mock_func = AsyncMock()
        
        task = ScheduledTask(
            name="test_task",
            func=mock_func,
            interval_minutes=30
        )
        
        assert task.name == "test_task"
        assert task.interval_minutes == 30
        assert task.daily_at_hour is None
        assert task.next_run is not None
        assert task.run_count == 0
        assert task.error_count == 0
        assert not task.is_running
    
    def test_daily_task_creation(self):
        """Test creating a daily task."""
        mock_func = AsyncMock()
        
        task = ScheduledTask(
            name="daily_task",
            func=mock_func,
            daily_at_hour=9
        )
        
        assert task.name == "daily_task"
        assert task.daily_at_hour == 9
        assert task.interval_minutes is None
        assert task.next_run is not None
    
    def test_invalid_task_configuration(self):
        """Test invalid task configurations."""
        mock_func = AsyncMock()
        
        # No timing specified
        with pytest.raises(ValueError, match="Must specify either"):
            ScheduledTask(name="invalid", func=mock_func)
        
        # Both timings specified
        with pytest.raises(ValueError, match="Cannot specify both"):
            ScheduledTask(
                name="invalid",
                func=mock_func,
                interval_minutes=30,
                daily_at_hour=9
            )
        
        # Invalid hour
        with pytest.raises(ValueError, match="daily_at_hour must be between"):
            ScheduledTask(
                name="invalid",
                func=mock_func,
                daily_at_hour=25
            )
    
    def test_should_run_logic(self):
        """Test task should_run logic."""
        mock_func = AsyncMock()
        now = datetime.now(timezone.utc)
        
        task = ScheduledTask(
            name="test_task",
            func=mock_func,
            interval_minutes=60
        )
        
        # Should not run if next_run is in the future
        task.next_run = now + timedelta(minutes=30)
        assert not task.should_run(now)
        
        # Should run if next_run is in the past
        task.next_run = now - timedelta(minutes=5)
        assert task.should_run(now)
        
        # Should not run if already running
        task.is_running = True
        assert not task.should_run(now)
    
    @pytest.mark.asyncio
    async def test_task_execution_success(self):
        """Test successful task execution."""
        mock_func = AsyncMock()
        
        task = ScheduledTask(
            name="test_task",
            func=mock_func,
            interval_minutes=30
        )
        
        result = await task.execute()
        
        assert result is True
        assert task.run_count == 1
        assert task.error_count == 0
        assert task.last_run is not None
        mock_func.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_task_execution_failure(self):
        """Test task execution with error."""
        mock_func = AsyncMock(side_effect=Exception("Test error"))
        
        task = ScheduledTask(
            name="test_task",
            func=mock_func,
            interval_minutes=30
        )
        
        result = await task.execute()
        
        assert result is False
        assert task.run_count == 0
        assert task.error_count == 1
        assert task.last_run is not None
    
    def test_task_status(self):
        """Test task status reporting."""
        mock_func = AsyncMock()
        
        task = ScheduledTask(
            name="test_task",
            func=mock_func,
            interval_minutes=30
        )
        
        status = task.get_status()
        
        assert status["name"] == "test_task"
        assert status["is_running"] is False
        assert status["run_count"] == 0
        assert status["error_count"] == 0
        assert status["success_rate"] == 0


class TestTaskScheduler:
    """Test the TaskScheduler class."""
    
    def test_scheduler_initialization(self):
        """Test scheduler initialization."""
        scheduler = TaskScheduler()
        
        assert scheduler.tasks == []
        assert not scheduler.is_running
        assert scheduler._scheduler_task is None
    
    def test_add_task(self):
        """Test adding tasks to scheduler."""
        scheduler = TaskScheduler()
        mock_func = AsyncMock()
        
        task = scheduler.add_task(
            name="test_task",
            func=mock_func,
            interval_minutes=30
        )
        
        assert len(scheduler.tasks) == 1
        assert scheduler.tasks[0] is task
        assert task.name == "test_task"
    
    def test_add_duplicate_task(self):
        """Test adding duplicate task names."""
        scheduler = TaskScheduler()
        mock_func = AsyncMock()
        
        scheduler.add_task(
            name="test_task",
            func=mock_func,
            interval_minutes=30
        )
        
        with pytest.raises(ValueError, match="already exists"):
            scheduler.add_task(
                name="test_task",
                func=mock_func,
                interval_minutes=60
            )
    
    def test_remove_task(self):
        """Test removing tasks from scheduler."""
        scheduler = TaskScheduler()
        mock_func = AsyncMock()
        
        scheduler.add_task(
            name="test_task",
            func=mock_func,
            interval_minutes=30
        )
        
        # Remove existing task
        assert scheduler.remove_task("test_task") is True
        assert len(scheduler.tasks) == 0
        
        # Remove non-existent task
        assert scheduler.remove_task("non_existent") is False
    
    def test_get_task(self):
        """Test getting tasks by name."""
        scheduler = TaskScheduler()
        mock_func = AsyncMock()
        
        added_task = scheduler.add_task(
            name="test_task",
            func=mock_func,
            interval_minutes=30
        )
        
        # Get existing task
        found_task = scheduler.get_task("test_task")
        assert found_task is added_task
        
        # Get non-existent task
        assert scheduler.get_task("non_existent") is None
    
    @pytest.mark.asyncio
    async def test_run_task_now(self):
        """Test manually running a task."""
        scheduler = TaskScheduler()
        mock_func = AsyncMock()
        
        scheduler.add_task(
            name="test_task",
            func=mock_func,
            interval_minutes=30
        )
        
        # Run existing task
        result = await scheduler.run_task_now("test_task")
        assert result is True
        mock_func.assert_called_once()
        
        # Run non-existent task
        result = await scheduler.run_task_now("non_existent")
        assert result is False
    
    def test_scheduler_status(self):
        """Test scheduler status reporting."""
        scheduler = TaskScheduler()
        mock_func = AsyncMock()
        
        scheduler.add_task(
            name="task1",
            func=mock_func,
            interval_minutes=30
        )
        scheduler.add_task(
            name="task2",
            func=mock_func,
            daily_at_hour=9
        )
        
        status = scheduler.get_status()
        
        assert status["is_running"] is False
        assert status["total_tasks"] == 2
        assert len(status["tasks"]) == 2
        assert status["next_task_run"] is not None


class TestGlobalScheduler:
    """Test the global scheduler functionality."""
    
    def test_get_scheduler_singleton(self):
        """Test that get_scheduler returns singleton."""
        scheduler1 = get_scheduler()
        scheduler2 = get_scheduler()
        
        assert scheduler1 is scheduler2
        assert isinstance(scheduler1, TaskScheduler)


@pytest.mark.asyncio
async def test_scheduler_start_stop():
    """Test scheduler start and stop functionality."""
    scheduler = TaskScheduler()
    
    # Start scheduler
    await scheduler.start()
    assert scheduler.is_running is True
    assert scheduler._scheduler_task is not None
    
    # Stop scheduler
    await scheduler.stop()
    assert scheduler.is_running is False