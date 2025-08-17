#!/usr/bin/env python3
"""
CLI wrapper for article fetching.

This script wraps the fetch_all_sources() function from the scheduler
for direct execution in GitHub Actions.
"""

import asyncio
import os
import sys
import time
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.services.scheduler import get_scheduler, setup_default_tasks


async def main() -> None:
    """CLI wrapper for article fetching with portfolio-friendly output."""
    start_time = time.time()
    print(f"🚀 Starting article fetch at {datetime.utcnow().isoformat()}Z")

    try:
        # Setup creates the inner functions and registers tasks
        await setup_default_tasks()
        scheduler = get_scheduler()

        # Get task for monitoring
        task = scheduler.get_task("fetch_articles")
        if task:
            print(f"📋 Task: {task.name} | Interval: {task.interval_minutes}min")

        # Execute using task name (calls the inner fetch_all_sources)
        success = await scheduler.run_task_now("fetch_articles")
        execution_time = time.time() - start_time

        if success:
            print(f"✅ Article fetch completed in {execution_time:.2f}s")

            # GitHub Actions summary output
            summary = "## 📰 Article Fetch Summary\n"
            summary += "- **Status**: ✅ Success\n"
            summary += f"- **Duration**: {execution_time:.2f}s\n"
            summary += f"- **Timestamp**: {datetime.utcnow().isoformat()}Z\n"

            # Write to GitHub step summary if available
            summary_file = os.getenv("GITHUB_STEP_SUMMARY")
            if summary_file:
                with open(summary_file, "a") as f:
                    f.write(summary)
        else:
            print(f"❌ Article fetch failed after {execution_time:.2f}s")

        sys.exit(0 if success else 1)

    except Exception as e:
        execution_time = time.time() - start_time
        print(f"❌ Fetch failed after {execution_time:.2f}s: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
