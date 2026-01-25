from sqlalchemy.orm import Session
from datetime import datetime
import logging

from services.scrapers.wholesome_co_scraper import WholesomeCoScraper
from services.product_matcher import ProductMatcher
from models import Product, Price, Dispensary

logger = logging.getLogger(__name__)

class ScraperRunner:
    """Runs scrapers and saves data to database"""

    def __init__(self, db: Session):
        self.db = db

    async def run_wholesomeco(self):
        """Run WholesomeCo scraper and save results"""
        logger.info("Starting WholesomeCo import...")
        
        # 1. Run Scraper
        scraper = WholesomeCoScraper(dispensary_id="wholesome-co")
        products = await scraper.scrape_products()
        
        if not products:
            logger.warning("No products found! Aborting save.")
            return {"status": "warning", "message": "No products found", "count": 0}

        logger.info(f"Scraped {len(products)} products. Saving to DB...")

        # 2. Get Dispensary Reference
        dispensary = self._get_or_create_dispensary(
            name="WholesomeCo",
            location="Bountiful, UT" # WholesomeCo is in Bountiful
        )

        # 3. Process Each Product
        matcher = ProductMatcher(self.db)
        
        for scraped in products:
            # Match or Create Product
            product = matcher.match_or_create(scraped)

            # Update Price
            self._update_price(product, dispensary, scraped.price, scraped.in_stock)

        self.db.commit()
        logger.info("✅ Database import complete!")
        
        return {
            "status": "success",
            "products_found": len(products),
            "dispensary": "WholesomeCo"
        }

    def _get_or_create_dispensary(self, name: str, location: str) -> Dispensary:
        dispensary = self.db.query(Dispensary).filter(Dispensary.name == name).first()
        if not dispensary:
            dispensary = Dispensary(name=name, location=location)
            self.db.add(dispensary)
            self.db.flush()
        return dispensary

    def _update_price(self, product: Product, dispensary: Dispensary, amount: float, in_stock: bool):
        price = self.db.query(Price).filter(
            Price.product_id == product.id,
            Price.dispensary_id == dispensary.id
        ).first()

        if price:
            # Update existing
            if price.amount != amount or price.in_stock != in_stock:
                price.update_price(amount)
                price.in_stock = in_stock
                price.last_updated = datetime.utcnow()
        else:
            # Create new
            new_price = Price(product_id=product.id, dispensary_id=dispensary.id, amount=amount, in_stock=in_stock)
            self.db.add(new_price)