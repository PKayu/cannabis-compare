"""
APScheduler integration for recurring scraper jobs.

Manages scheduled execution of dispensary scrapers with:
- Configurable intervals (default: 2 hours per PRD requirement)
- Automatic retry on failure
- Job management (add, remove, pause, resume)
- Logging and monitoring
- Auto-registration of all scrapers from ScraperRegistry
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
from services.scrapers.registry import ScraperRegistry

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


def register_all_scrapers(scheduler: ScraperScheduler) -> None:
    """
    Automatically register all enabled scrapers from the ScraperRegistry.

    This function iterates through all registered scrapers and adds them
    to the scheduler with their configured intervals. Called once at startup.

    Args:
        scheduler: The ScraperScheduler instance to register jobs with
    """
    registered_count = 0
    skipped_count = 0

    for config in ScraperRegistry.get_enabled():
        try:
            scheduler.add_scraper_job(
                scraper_class=config.scraper_class,
                dispensary_id=config.id,
                minutes=config.schedule_minutes,
                run_immediately=False
            )
            registered_count += 1
            logger.info(
                f"Scheduled {config.name} to run every {config.schedule_minutes} minutes"
            )
        except Exception as e:
            logger.error(f"Failed to schedule {config.name}: {e}")
            skipped_count += 1

    logger.info(
        f"Scheduled {registered_count} scrapers"
        + (f" ({skipped_count} skipped)" if skipped_count > 0 else "")
    )


# Alert detection job
def run_alert_checks():
    """Check for stock/price alerts and send emails"""
    from database import SessionLocal
    from models import User, NotificationPreference, Product, Dispensary, Price
    from services.alerts.stock_detector import StockDetector
    from services.alerts.price_detector import PriceDetector
    from services.notifications.email_service import EmailNotificationService

    print(f"[{datetime.now()}] Running alert checks...")
    db = SessionLocal()

    try:
        # Detect new alerts
        stock_alerts = StockDetector.check_stock_changes(db)
        price_alerts = PriceDetector.check_price_drops(db)

        print(f"  Found {len(stock_alerts)} stock alerts, {len(price_alerts)} price drop alerts")

        # Send emails based on user preferences
        for alert in stock_alerts + price_alerts:
            user = db.query(User).filter(User.id == alert.user_id).first()
            if not user:
                continue

            prefs = db.query(NotificationPreference).filter(
                NotificationPreference.user_id == user.id
            ).first()

            # Check if user wants emails for this alert type
            if prefs:
                if alert.alert_type == "stock_available" and not prefs.email_stock_alerts:
                    continue
                if alert.alert_type == "price_drop" and not prefs.email_price_drops:
                    continue

            # Only send immediate emails (daily/weekly handled separately)
            if not prefs or prefs.email_frequency == "immediately":
                product = db.query(Product).filter(Product.id == alert.product_id).first()
                dispensary = db.query(Dispensary).filter(Dispensary.id == alert.dispensary_id).first()
                price = db.query(Price).filter(
                    Price.product_id == alert.product_id,
                    Price.dispensary_id == alert.dispensary_id
                ).first()

                if product and dispensary and price:
                    # Send email
                    if alert.alert_type == "stock_available":
                        success = EmailNotificationService.send_stock_alert(
                            user, product, price, dispensary
                        )
                    elif alert.alert_type == "price_drop":
                        success = EmailNotificationService.send_price_drop_alert(
                            user, product, price, dispensary, alert.percent_change or 0
                        )
                    else:
                        success = False

                    if success:
                        alert.email_sent = True
                        db.commit()
                        print(f"  Sent {alert.alert_type} alert to {user.email}")
                    else:
                        print(f"  Failed to send {alert.alert_type} alert to {user.email}")

        print(f"[{datetime.now()}] Alert checks complete")

    except Exception as e:
        print(f"Error running alert checks: {e}")
        db.rollback()
    finally:
        db.close()


def start_alert_scheduler():
    """Start the alert detection scheduler"""
    from apscheduler.schedulers.background import BackgroundScheduler
    from config import settings

    scheduler = BackgroundScheduler()

    # Add alert check job (runs every 1-2 hours based on config)
    interval_hours = settings.alert_check_interval_hours
    scheduler.add_job(
        run_alert_checks,
        'interval',
        hours=interval_hours,
        id='alert_detection_job',
        name='Alert Detection Job',
        replace_existing=True
    )

    scheduler.start()
    print(f"Alert scheduler started - checking every {interval_hours} hour(s)")

    return scheduler
