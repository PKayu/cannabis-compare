"""
APScheduler integration for recurring scraper jobs.

Manages scheduled execution of dispensary scrapers with:
- Configurable intervals (default: 2 hours per PRD requirement)
- Automatic retry on failure
- Job management (add, remove, pause, resume)
- Logging and monitoring
"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.executors.asyncio import AsyncIOExecutor
from typing import Type, Dict, Optional, List
from datetime import datetime
import logging
import asyncio

from services.scrapers.base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class ScraperScheduler:
    """
    Manages scheduled scraper execution.

    Usage:
        scheduler = ScraperScheduler()
        scheduler.add_scraper_job(WholesomeCoScraper, "dispensary-id", minutes=120)
        await scheduler.start()
    """

    def __init__(self):
        """Initialize the scheduler with default configuration"""
        jobstores = {
            'default': MemoryJobStore()
        }
        executors = {
            'default': AsyncIOExecutor()
        }
        job_defaults = {
            'coalesce': True,  # Combine missed runs into one
            'max_instances': 1,  # Only one instance per scraper
            'misfire_grace_time': 300  # 5 minutes grace period
        }

        self.scheduler = AsyncIOScheduler(
            jobstores=jobstores,
            executors=executors,
            job_defaults=job_defaults
        )

        self._scrapers: Dict[str, dict] = {}  # Track registered scrapers
        self._is_running = False

    async def start(self):
        """Start the scheduler"""
        if self._is_running:
            logger.warning("Scheduler already running")
            return

        self.scheduler.start()
        self._is_running = True
        logger.info("Scraper scheduler started")

    async def stop(self, wait: bool = True):
        """
        Stop the scheduler.

        Args:
            wait: If True, wait for running jobs to complete
        """
        if not self._is_running:
            return

        self.scheduler.shutdown(wait=wait)
        self._is_running = False
        logger.info("Scraper scheduler stopped")

    def add_scraper_job(
        self,
        scraper_class: Type[BaseScraper],
        dispensary_id: str,
        minutes: int = 120,
        run_immediately: bool = False
    ) -> str:
        """
        Schedule a scraper to run at regular intervals.

        Args:
            scraper_class: The scraper class to use
            dispensary_id: ID of the dispensary to scrape
            minutes: Interval between runs (default: 120 = 2 hours)
            run_immediately: If True, run once immediately

        Returns:
            Job ID for management
        """
        job_id = f"scraper_{dispensary_id}"

        # Remove existing job if present
        if job_id in self._scrapers:
            self.remove_scraper_job(dispensary_id)

        # Create scraper instance
        scraper = scraper_class(dispensary_id)

        # Add job to scheduler
        job = self.scheduler.add_job(
            func=self._run_scraper,
            trigger=IntervalTrigger(minutes=minutes),
            id=job_id,
            name=f"{scraper.name} for {dispensary_id}",
            args=[scraper],
            replace_existing=True
        )

        # Track scraper info
        self._scrapers[job_id] = {
            "dispensary_id": dispensary_id,
            "scraper_class": scraper_class.__name__,
            "interval_minutes": minutes,
            "job": job,
            "scraper": scraper,
            "added_at": datetime.utcnow()
        }

        logger.info(
            f"Scheduled {scraper.name} for {dispensary_id} "
            f"every {minutes} minutes"
        )

        # Run immediately if requested
        if run_immediately:
            asyncio.create_task(self._run_scraper(scraper))

        return job_id

    def add_daily_job(
        self,
        scraper_class: Type[BaseScraper],
        dispensary_id: str,
        hour: int = 6,
        minute: int = 0
    ) -> str:
        """
        Schedule a scraper to run once daily at a specific time.

        Args:
            scraper_class: The scraper class to use
            dispensary_id: ID of the dispensary to scrape
            hour: Hour to run (0-23, default: 6 AM)
            minute: Minute to run (0-59, default: 0)

        Returns:
            Job ID for management
        """
        job_id = f"scraper_daily_{dispensary_id}"

        scraper = scraper_class(dispensary_id)

        job = self.scheduler.add_job(
            func=self._run_scraper,
            trigger=CronTrigger(hour=hour, minute=minute),
            id=job_id,
            name=f"Daily {scraper.name} for {dispensary_id}",
            args=[scraper],
            replace_existing=True
        )

        self._scrapers[job_id] = {
            "dispensary_id": dispensary_id,
            "scraper_class": scraper_class.__name__,
            "schedule": f"Daily at {hour:02d}:{minute:02d}",
            "job": job,
            "scraper": scraper,
            "added_at": datetime.utcnow()
        }

        logger.info(
            f"Scheduled daily {scraper.name} for {dispensary_id} "
            f"at {hour:02d}:{minute:02d}"
        )

        return job_id

    def remove_scraper_job(self, dispensary_id: str) -> bool:
        """
        Remove a scheduled scraper job.

        Args:
            dispensary_id: ID of the dispensary

        Returns:
            True if job was removed, False if not found
        """
        job_id = f"scraper_{dispensary_id}"

        if job_id not in self._scrapers:
            # Try daily job id
            job_id = f"scraper_daily_{dispensary_id}"

        if job_id in self._scrapers:
            try:
                self.scheduler.remove_job(job_id)
            except Exception:
                pass
            del self._scrapers[job_id]
            logger.info(f"Removed scraper job for {dispensary_id}")
            return True

        return False

    def pause_scraper(self, dispensary_id: str) -> bool:
        """Pause a scraper job"""
        job_id = f"scraper_{dispensary_id}"
        if job_id in self._scrapers:
            self.scheduler.pause_job(job_id)
            logger.info(f"Paused scraper for {dispensary_id}")
            return True
        return False

    def resume_scraper(self, dispensary_id: str) -> bool:
        """Resume a paused scraper job"""
        job_id = f"scraper_{dispensary_id}"
        if job_id in self._scrapers:
            self.scheduler.resume_job(job_id)
            logger.info(f"Resumed scraper for {dispensary_id}")
            return True
        return False

    async def run_scraper_now(self, dispensary_id: str) -> Optional[dict]:
        """
        Manually trigger a scraper run.

        Args:
            dispensary_id: ID of the dispensary to scrape

        Returns:
            Scraper result or None if scraper not found
        """
        job_id = f"scraper_{dispensary_id}"
        if job_id in self._scrapers:
            scraper = self._scrapers[job_id]["scraper"]
            return await self._run_scraper(scraper)
        return None

    async def _run_scraper(self, scraper: BaseScraper) -> dict:
        """
        Execute a scraper with error handling.

        This is the function called by the scheduler.
        """
        logger.info(f"Running {scraper.name}")

        try:
            result = await scraper.run_with_retries(max_retries=3)

            if result["status"] == "success":
                # Process results (update database, etc.)
                await self._process_scraper_results(result)
            else:
                logger.error(
                    f"{scraper.name} failed: {result.get('error', 'Unknown error')}"
                )

            return result

        except Exception as e:
            logger.exception(f"Unexpected error running {scraper.name}: {e}")
            return {
                "dispensary_id": scraper.dispensary_id,
                "status": "error",
                "error": str(e)
            }

    async def _process_scraper_results(self, result: dict):
        """
        Process scraper results and update database.

        This method should be overridden or extended to handle
        database updates based on scraper results.
        """
        # Import here to avoid circular imports
        # This would typically use ConfidenceScorer to process products

        products = result.get("products", [])
        promotions = result.get("promotions", [])

        logger.info(
            f"Processing {len(products)} products and {len(promotions)} promotions "
            f"for {result['dispensary_id']}"
        )

        # TODO: Integrate with ConfidenceScorer to process products
        # and update Price/Promotion tables

    def get_all_jobs(self) -> List[dict]:
        """Get information about all scheduled jobs"""
        jobs = []
        for job_id, info in self._scrapers.items():
            job = info["job"]
            jobs.append({
                "job_id": job_id,
                "dispensary_id": info["dispensary_id"],
                "scraper": info["scraper_class"],
                "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
                "is_paused": job.next_run_time is None,
                "last_run": info["scraper"].get_last_run(),
                "interval": info.get("interval_minutes", info.get("schedule", "N/A"))
            })
        return jobs

    def get_job_status(self, dispensary_id: str) -> Optional[dict]:
        """Get status of a specific scraper job"""
        job_id = f"scraper_{dispensary_id}"
        if job_id in self._scrapers:
            info = self._scrapers[job_id]
            job = info["job"]
            scraper = info["scraper"]
            return {
                "job_id": job_id,
                "dispensary_id": info["dispensary_id"],
                "scraper": info["scraper_class"],
                "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
                "is_paused": job.next_run_time is None,
                "last_run": scraper.get_last_run(),
                "last_result_status": (
                    scraper.get_last_result().get("status")
                    if scraper.get_last_result() else None
                ),
                "interval_minutes": info.get("interval_minutes"),
                "added_at": info["added_at"].isoformat()
            }
        return None

    @property
    def is_running(self) -> bool:
        """Check if scheduler is running"""
        return self._is_running

    @property
    def job_count(self) -> int:
        """Get number of scheduled jobs"""
        return len(self._scrapers)


# Global scheduler instance
_scheduler: Optional[ScraperScheduler] = None


def get_scheduler() -> ScraperScheduler:
    """Get or create the global scheduler instance"""
    global _scheduler
    if _scheduler is None:
        _scheduler = ScraperScheduler()
    return _scheduler
