"""
Scraper Runner - Executes scrapers and saves results to database.

This service coordinates scraping operations:
1. Instantiates the scraper from the registry
2. Executes the scrape
3. Processes products through ConfidenceScorer (fuzzy matching + variants)
4. Updates prices in the database

Usage:
    runner = ScraperRunner(db)
    result = await runner.run_by_id("wholesomeco")
    # or run all scrapers:
    results = await runner.run_all()
"""
from datetime import datetime
from typing import Dict, Any, Optional
import logging

from sqlalchemy.orm import Session

from models import Product, Price, Dispensary, ScraperRun
from services.normalization.scorer import ConfidenceScorer
from services.scrapers.registry import ScraperRegistry

logger = logging.getLogger(__name__)


class ScraperRunner:
    """
    Runs scrapers and saves data to database.

    Uses the ScraperRegistry to dynamically instantiate and run
    any registered scraper by its ID.
    """

    def __init__(self, db: Session, triggered_by: str = "manual"):
        """
        Initialize the scraper runner.

        Args:
            db: SQLAlchemy database session
            triggered_by: Who triggered the run ("scheduler", "manual", or admin user id)
        """
        self.db = db
        self.triggered_by = triggered_by

    async def run_by_id(self, scraper_id: str) -> Dict[str, Any]:
        """
        Run a scraper by its registry ID and save results to database.

        Every execution is logged to the scraper_runs table for monitoring.

        Args:
            scraper_id: The scraper's registry ID (e.g., "wholesomeco", "beehive")

        Returns:
            Dict containing:
                - status: "success" | "error" | "warning"
                - products_found: Number of products scraped
                - dispensary: Name of the dispensary
                - error: Error message if status is "error"
                - run_id: ID of the ScraperRun log entry

        Raises:
            ValueError: If scraper_id is not found in registry
        """
        config = ScraperRegistry.get(scraper_id)

        if not config:
            raise ValueError(
                f"Unknown scraper: '{scraper_id}'. "
                f"Available scrapers: {list(ScraperRegistry.get_all().keys())}"
            )

        if not config.enabled:
            logger.warning(f"Scraper '{scraper_id}' is disabled")
            return {
                "status": "error",
                "error": f"Scraper '{scraper_id}' is disabled",
                "scraper_id": scraper_id
            }

        # Create run log entry and commit immediately so it's visible
        # to other sessions (e.g., admin dashboard polling for status)
        run_log = ScraperRun(
            scraper_id=scraper_id,
            scraper_name=config.name,
            triggered_by=self.triggered_by,
            status="running"
        )
        self.db.add(run_log)
        self.db.commit()
        self.db.refresh(run_log)

        logger.info(f"Starting {config.name} scraper (run_id={run_log.id})...")

        try:
            # 1. Instantiate and run the scraper
            logger.info(f"Instantiating scraper class: {config.scraper_class}")
            logger.info(f"Scraper module: {config.scraper_class.__module__}")
            logger.info(f"Scraper name: {config.scraper_class.__name__}")
            scraper = config.scraper_class(dispensary_id=scraper_id)
            logger.info(f"Scraper instantiated successfully: {scraper}")
            logger.info(f"Calling scrape_products()...")
            products = await scraper.scrape_products()
            logger.info(f"scrape_products() returned {len(products)} products")

            if not products:
                logger.warning(f"No products found for {config.name}")
                run_log.complete(status="warning")
                self.db.commit()
                return {
                    "status": "warning",
                    "message": "No products found",
                    "count": 0,
                    "scraper_id": scraper_id,
                    "run_id": run_log.id
                }

            logger.info(f"Scraped {len(products)} products from {config.name}. Saving to DB...")

            # 2. Get or create the dispensary record
            dispensary = self._get_or_create_dispensary(
                name=config.dispensary_name,
                location=config.dispensary_location
            )

            # Link run log to dispensary now that we have it
            run_log.dispensary_id = dispensary.id

            # 3. Pre-load master product candidates for fuzzy matching
            master_products = (
                self.db.query(Product)
                .filter(Product.is_master.is_(True))
                .all()
            )
            candidates = [
                {
                    "id": m.id,
                    "name": m.name,
                    "brand": m.brand.name if m.brand else "",
                    "thc_percentage": m.thc_percentage
                }
                for m in master_products
            ]

            # 4. Process each product through ConfidenceScorer
            processed_count = 0
            flags_created = 0

            for scraped in products:
                # Create savepoint before processing each product
                # This allows per-product rollback without losing entire batch
                savepoint = self.db.begin_nested()
                try:
                    product_id, action = ConfidenceScorer.process_scraped_product(
                        db=self.db,
                        scraped_product=scraped,
                        dispensary_id=dispensary.id,
                        candidates=candidates
                    )

                    if action == "flagged_review":
                        flags_created += 1
                        savepoint.commit()  # Commit the flag creation
                        continue  # Don't create price for flagged products

                    if product_id:
                        product = self.db.query(Product).filter(
                            Product.id == product_id
                        ).first()
                        if product:
                            self._update_price(
                                product,
                                dispensary,
                                scraped.price,
                                scraped.in_stock,
                                scraped.url
                            )
                            processed_count += 1

                    savepoint.commit()  # Commit this product's changes

                except Exception as e:
                    logger.error(
                        f"Failed to process product '{scraped.name}': {e}",
                        exc_info=True
                    )
                    # Rollback ONLY this product's changes, not the entire batch
                    savepoint.rollback()
                    continue

            # 5. Complete run log and commit all changes
            run_log.complete(
                status="success",
                products_found=len(products),
                products_processed=processed_count,
                flags_created=flags_created
            )

            # Explicit commit with error handling
            try:
                self.db.commit()
                logger.info(f"Database import complete for {config.name}! " +
                           f"Processed: {processed_count}, Flags: {flags_created}")
            except Exception as commit_error:
                logger.error(f"Failed to commit scraper run: {commit_error}", exc_info=True)
                self.db.rollback()
                raise  # Re-raise to mark run as failed

            return {
                "status": "success",
                "products_found": len(products),
                "products_processed": processed_count,
                "dispensary": config.dispensary_name,
                "scraper_id": scraper_id,
                "run_id": run_log.id
            }

        except Exception as e:
            logger.error(f"Scraper {scraper_id} failed: {e}", exc_info=True)
            run_log.complete(
                status="error",
                error_message=str(e),
                error_type=type(e).__name__
            )
            self.db.commit()
            return {
                "status": "error",
                "error": str(e),
                "scraper_id": scraper_id,
                "run_id": run_log.id
            }

    async def run_all(self) -> Dict[str, Any]:
        """
        Run all enabled scrapers and save results to database.

        Returns:
            Dict mapping scraper IDs to their results
        """
        results = {}

        for config in ScraperRegistry.get_enabled():
            try:
                result = await self.run_by_id(config.id)
                results[config.id] = result
            except Exception as e:
                logger.error(f"Failed to run {config.name}: {e}")
                results[config.id] = {
                    "status": "error",
                    "error": str(e),
                    "scraper_id": config.id
                }

        return results

    # ========== Backwards Compatibility Methods ==========

    async def run_wholesomeco(self) -> Dict[str, Any]:
        """
        Run WholesomeCo scraper (backwards compatibility).

        Deprecated: Use run_by_id("wholesomeco") instead.
        """
        return await self.run_by_id("wholesomeco")

    # ========== Helper Methods ==========

    def _get_or_create_dispensary(self, name: str, location: str) -> Dispensary:
        """
        Get existing dispensary or create a new one.

        Args:
            name: Dispensary name
            location: Dispensary location

        Returns:
            Dispensary database record
        """
        dispensary = self.db.query(Dispensary).filter(
            Dispensary.name == name
        ).first()

        if not dispensary:
            dispensary = Dispensary(name=name, location=location)
            self.db.add(dispensary)
            self.db.flush()

        return dispensary

    def _update_price(
        self,
        product: Product,
        dispensary: Dispensary,
        amount: float,
        in_stock: bool,
        product_url: Optional[str] = None
    ) -> None:
        """
        Update or create price record for a product at a dispensary.

        Args:
            product: Product database record
            dispensary: Dispensary database record
            amount: Price amount
            in_stock: Whether the product is in stock
            product_url: Direct link to product page at dispensary
        """
        # First check in session (for newly added but uncommitted prices)
        for obj in self.db.new:
            if isinstance(obj, Price):
                if obj.product_id == product.id and obj.dispensary_id == dispensary.id:
                    # Price already added to session, update it
                    if obj.amount != amount or obj.in_stock != in_stock or obj.product_url != product_url:
                        obj.amount = amount
                        obj.in_stock = in_stock
                        obj.product_url = product_url
                        obj.last_updated = datetime.utcnow()
                    return

        # Check in database
        price = self.db.query(Price).filter(
            Price.product_id == product.id,
            Price.dispensary_id == dispensary.id
        ).first()

        if price:
            # Update existing price if changed
            if price.amount != amount or price.in_stock != in_stock or price.product_url != product_url:
                price.update_price(amount)
                price.in_stock = in_stock
                price.product_url = product_url
                price.last_updated = datetime.utcnow()
        else:
            # Create new price record
            new_price = Price(
                product_id=product.id,
                dispensary_id=dispensary.id,
                amount=amount,
                in_stock=in_stock,
                product_url=product_url
            )
            self.db.add(new_price)
