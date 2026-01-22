---
description: Build abstract base scraper class, implement fuzzy matching normalization (>90%/60-90%/<60% confidence levels), and create first Utah dispensary scraper.
auto_execution_mode: 1
---

## Context

This workflow implements the core data aggregation engine as defined in PRD sections 4.1 and 4.2:
- Confidence-based product matching and normalization
- Support for iHeartJane and Dutchie menu providers
- Scheduled recurring scrapes (≤2 hour update frequency)
- Historical pricing tracking and promotion capture

## Steps

### 1. Review Scraping Requirements

Read PRD sections 4.1-4.2:
- Automated ingestion from iHeartJane, Dutchie, and proprietary APIs
- >80% auto-merge rate target
- <2 hour update frequency
- Promo scraping (specials, discounts, recurring deals)

### 2. Create Abstract BaseScraper Class

Create `backend/services/scrapers/base_scraper.py`:

```python
"""Abstract base class for all dispensary scrapers"""
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional, Dict
import logging

logger = logging.getLogger(__name__)

class Product(ABC):
    """Standard product data structure"""
    name: str
    brand: str
    category: str  # "Flower", "Vape", "Edible", etc.
    thc_percentage: Optional[float]
    cbd_percentage: Optional[float]
    price: float
    in_stock: bool
    batch_number: Optional[str]
    cultivation_date: Optional[datetime]

class Promotion(ABC):
    """Standard promotion data structure"""
    title: str
    description: Optional[str]
    discount_percentage: Optional[float]
    discount_amount: Optional[float]
    applies_to: Optional[str]  # "Flower", product_id, or None (all)
    start_date: datetime
    end_date: Optional[datetime]
    is_recurring: bool
    recurring_day: Optional[str]  # "monday", "friday", etc.

class BaseScraper(ABC):
    """Base class for all dispensary scrapers"""

    def __init__(self, dispensary_id: str, logger: Optional[logging.Logger] = None):
        self.dispensary_id = dispensary_id
        self.logger = logger or logging.getLogger(self.__class__.__name__)

    @abstractmethod
    async def scrape_products(self) -> List[Product]:
        """Scrape current inventory"""
        pass

    @abstractmethod
    async def scrape_promotions(self) -> List[Promotion]:
        """Scrape current promotions"""
        pass

    async def run(self) -> Dict[str, any]:
        """Execute scrape and return results"""
        try:
            products = await self.scrape_products()
            promotions = await self.scrape_promotions()

            self.logger.info(
                f"Scraped {len(products)} products, {len(promotions)} promotions"
            )

            return {
                "dispensary_id": self.dispensary_id,
                "products": products,
                "promotions": promotions,
                "scraped_at": datetime.utcnow(),
                "status": "success"
            }
        except Exception as e:
            self.logger.error(f"Scrape failed: {e}")
            return {
                "dispensary_id": self.dispensary_id,
                "status": "error",
                "error": str(e)
            }
```

### 3. Implement Fuzzy Matching Library

Create `backend/services/normalization/matcher.py`:

```python
"""Fuzzy matching and confidence scoring for product normalization"""
from rapidfuzz import fuzz
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)

class ProductMatcher:
    """Matches scraped products to existing master products"""

    # Confidence thresholds (PRD section 4.1)
    AUTO_MERGE_THRESHOLD = 0.90     # >90% = automatic merge
    REVIEW_THRESHOLD = 0.60         # 60-90% = flag for review
    NEW_PRODUCT_THRESHOLD = 0.60    # <60% = create new entry

    @staticmethod
    def score_match(
        scraped_name: str,
        master_name: str,
        scraped_brand: str,
        master_brand: str,
        scraped_thc: Optional[float] = None,
        master_thc: Optional[float] = None
    ) -> Tuple[float, str]:
        """
        Calculate match confidence score.
        Returns: (confidence_score, match_type)
        """

        # Name similarity (70% weight)
        name_similarity = fuzz.token_sort_ratio(
            scraped_name.lower(),
            master_name.lower()
        ) / 100.0

        # Brand similarity (20% weight)
        brand_similarity = fuzz.token_sort_ratio(
            scraped_brand.lower(),
            master_brand.lower()
        ) / 100.0

        # THC similarity (10% weight)
        thc_similarity = 1.0
        if scraped_thc and master_thc:
            thc_diff = abs(scraped_thc - master_thc)
            thc_similarity = max(0, 1.0 - (thc_diff / 30))  # 30% diff = 0 score

        # Weighted score
        confidence = (
            name_similarity * 0.70 +
            brand_similarity * 0.20 +
            thc_similarity * 0.10
        )

        # Determine match type
        if confidence >= ProductMatcher.AUTO_MERGE_THRESHOLD:
            match_type = "auto_merge"
        elif confidence >= ProductMatcher.REVIEW_THRESHOLD:
            match_type = "flagged_review"
        else:
            match_type = "new_product"

        logger.debug(
            f"Match score: {confidence:.2f} ({match_type}) - "
            f"{scraped_name} vs {master_name}"
        )

        return confidence, match_type

    @staticmethod
    def normalize_product_name(name: str) -> str:
        """Normalize product names for comparison"""
        return (
            name.lower()
            .strip()
            .replace("  ", " ")
            .replace("®", "")
            .replace("™", "")
        )

    @staticmethod
    def normalize_brand_name(name: str) -> str:
        """Normalize brand names"""
        return (
            name.lower()
            .strip()
            .replace("inc.", "")
            .replace("llc", "")
            .replace("  ", " ")
        )
```

### 4. Build Confidence Scoring System

Create `backend/services/normalization/scorer.py`:

```python
"""Confidence scoring and ScraperFlag creation"""
from sqlalchemy.orm import Session
from backend.models import ScraperFlag, Product
from backend.services.normalization.matcher import ProductMatcher
from typing import Optional

class ConfidenceScorer:
    """Manages confidence-based product matching"""

    @staticmethod
    async def process_scraped_product(
        db: Session,
        scraped_product,
        dispensary_id: str
    ) -> Optional[str]:
        """
        Process a scraped product and return the product_id to link to Price table.

        Returns:
        - product_id if match found or created
        - None if flagged for review
        """

        # Find best matching master product
        master_products = db.query(Product).filter(
            Product.is_master == True
        ).all()

        best_match = None
        best_score = 0

        for master in master_products:
            score, _ = ProductMatcher.score_match(
                scraped_product.name,
                master.name,
                scraped_product.brand,
                master.brand,
                scraped_product.thc_percentage,
                master.thc_percentage
            )

            if score > best_score:
                best_score = score
                best_match = master

        _, match_type = ProductMatcher.score_match(
            scraped_product.name,
            best_match.name if best_match else scraped_product.name,
            scraped_product.brand,
            best_match.brand if best_match else scraped_product.brand,
            scraped_product.thc_percentage,
            best_match.thc_percentage if best_match else None
        )

        if match_type == "auto_merge" and best_match:
            # AUTO-MERGE: Link directly to existing product
            return best_match.id

        elif match_type == "flagged_review":
            # FLAGGED FOR REVIEW: Create ScraperFlag for admin approval
            flag = ScraperFlag(
                original_name=scraped_product.name,
                original_thc=scraped_product.thc_percentage,
                original_cbd=scraped_product.cbd_percentage,
                brand_name=scraped_product.brand,
                dispensary_id=dispensary_id,
                matched_product_id=best_match.id if best_match else None,
                confidence_score=best_score,
                status="pending"
            )
            db.add(flag)
            db.commit()
            return None

        else:
            # NEW PRODUCT: Create master product entry
            new_product = Product(
                name=scraped_product.name,
                product_type=scraped_product.category,
                brand_id=self._get_or_create_brand(db, scraped_product.brand),
                thc_percentage=scraped_product.thc_percentage,
                cbd_percentage=scraped_product.cbd_percentage,
                is_master=True,
                normalization_confidence=1.0
            )
            db.add(new_product)
            db.commit()
            return new_product.id

    @staticmethod
    def _get_or_create_brand(db: Session, brand_name: str):
        """Get or create brand by name"""
        from backend.models import Brand
        brand = db.query(Brand).filter(Brand.name == brand_name).first()
        if not brand:
            brand = Brand(name=brand_name)
            db.add(brand)
            db.commit()
        return brand.id
```

### 5. Create ScraperFlag Workflow

Create `backend/services/normalization/flag_processor.py`:

```python
"""Process and resolve ScraperFlags created by the scraper"""
from sqlalchemy.orm import Session
from backend.models import ScraperFlag, Product, Price
from datetime import datetime
from typing import Literal

class ScraperFlagProcessor:
    """Handles admin approval/rejection of flagged products"""

    @staticmethod
    async def approve_flag(
        db: Session,
        flag_id: str,
        admin_id: str,
        notes: str = ""
    ) -> str:
        """Approve merge of flagged product to matched product"""
        flag = db.query(ScraperFlag).filter(ScraperFlag.id == flag_id).first()
        if not flag or not flag.matched_product_id:
            raise ValueError("Invalid flag or no matched product")

        flag.status = "approved"
        flag.resolved_by = admin_id
        flag.resolved_at = datetime.utcnow()
        flag.admin_notes = notes
        db.commit()

        return flag.matched_product_id

    @staticmethod
    async def reject_flag(
        db: Session,
        flag_id: str,
        admin_id: str,
        notes: str = ""
    ) -> None:
        """Reject merge and create new product from flagged entry"""
        flag = db.query(ScraperFlag).filter(ScraperFlag.id == flag_id).first()
        if not flag:
            raise ValueError("Invalid flag")

        # Create new product from flag data
        new_product = Product(
            name=flag.original_name,
            product_type="Unknown",  # Set during review
            brand_id=self._get_or_create_brand(flag.brand_name),
            thc_percentage=flag.original_thc,
            cbd_percentage=flag.original_cbd,
            is_master=True,
            normalization_confidence=1.0
        )
        db.add(new_product)

        flag.status = "rejected"
        flag.resolved_by = admin_id
        flag.resolved_at = datetime.utcnow()
        flag.admin_notes = notes

        db.commit()

    @staticmethod
    def get_pending_flags(db: Session, limit: int = 50):
        """Get flags pending admin review"""
        return (
            db.query(ScraperFlag)
            .filter(ScraperFlag.status == "pending")
            .order_by(ScraperFlag.created_at.desc())
            .limit(limit)
            .all()
        )
```

### 6. Implement First Dispensary Scraper (WholesomeCo)

Create `backend/services/scrapers/wholesome_co_scraper.py`:

```python
"""Scraper for WholesomeCo Utah dispensary"""
import aiohttp
import logging
from typing import List
from bs4 import BeautifulSoup
from backend.services.scrapers.base_scraper import BaseScraper, Product, Promotion
from datetime import datetime

logger = logging.getLogger(__name__)

class WholesomeCoScraper(BaseScraper):
    """Scrapes WholesomeCo menu and promotions"""

    BASE_URL = "https://www.wholesomeco.com"
    MENU_ENDPOINT = "/api/menu"

    async def scrape_products(self) -> List[Product]:
        """Scrape WholesomeCo inventory"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.BASE_URL}{self.MENU_ENDPOINT}"
                ) as resp:
                    data = await resp.json()
                    products = self._parse_menu(data)
                    self.logger.info(f"Scraped {len(products)} products from WholesomeCo")
                    return products
        except Exception as e:
            self.logger.error(f"Failed to scrape WholesomeCo menu: {e}")
            return []

    async def scrape_promotions(self) -> List[Promotion]:
        """Scrape WholesomeCo promotions"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.BASE_URL}/promotions"
                ) as resp:
                    html = await resp.text()
                    promotions = self._parse_promotions(html)
                    self.logger.info(f"Scraped {len(promotions)} promotions from WholesomeCo")
                    return promotions
        except Exception as e:
            self.logger.error(f"Failed to scrape WholesomeCo promotions: {e}")
            return []

    def _parse_menu(self, data: dict) -> List[Product]:
        """Parse menu JSON response"""
        products = []
        for item in data.get("items", []):
            try:
                product = Product(
                    name=item.get("name"),
                    brand=item.get("brand"),
                    category=item.get("category"),
                    thc_percentage=item.get("thc"),
                    cbd_percentage=item.get("cbd"),
                    price=float(item.get("price", 0)),
                    in_stock=item.get("in_stock", True),
                    batch_number=item.get("batch_id"),
                    cultivation_date=item.get("harvest_date")
                )
                products.append(product)
            except Exception as e:
                self.logger.warning(f"Failed to parse product: {e}")
        return products

    def _parse_promotions(self, html: str) -> List[Promotion]:
        """Parse promotions from HTML"""
        promotions = []
        soup = BeautifulSoup(html, "html.parser")

        for promo_elem in soup.find_all("div", class_="promotion"):
            try:
                promotion = Promotion(
                    title=promo_elem.find("h3").text,
                    description=promo_elem.find("p").text if promo_elem.find("p") else None,
                    discount_percentage=self._extract_discount(promo_elem),
                    start_date=datetime.utcnow(),
                    is_recurring=self._is_recurring(promo_elem),
                    recurring_day=self._extract_day(promo_elem)
                )
                promotions.append(promotion)
            except Exception as e:
                self.logger.warning(f"Failed to parse promotion: {e}")

        return promotions

    @staticmethod
    def _extract_discount(elem) -> float:
        """Extract discount percentage from element"""
        text = elem.find("span", class_="discount").text if elem.find("span", class_="discount") else "0%"
        return float(text.replace("%", "").strip())

    @staticmethod
    def _is_recurring(elem) -> bool:
        """Check if promotion is recurring"""
        return "every" in elem.text.lower() or "daily" in elem.text.lower()

    @staticmethod
    def _extract_day(elem) -> str:
        """Extract recurring day if applicable"""
        days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        text = elem.text.lower()
        for day in days:
            if day in text:
                return day
        return None
```

### 7. Add Price History Tracking

Update `backend/models.py` Price model:

```python
class Price(Base):
    # ... existing fields ...

    # Add history tracking
    previous_price = Column(Float, nullable=True)
    price_change_date = Column(DateTime, nullable=True)
    price_change_percentage = Column(Float, nullable=True)  # % change since last update

    def update_price(self, new_price: float):
        """Update price and track history"""
        if self.amount != new_price:
            self.previous_price = self.amount
            self.price_change_percentage = ((new_price - self.amount) / self.amount) * 100 if self.amount else 0
            self.price_change_date = datetime.utcnow()
            self.amount = new_price
```

### 8. Build Promotion Scraper Logic

Update scrapers to capture and store promotions in database during run.

### 9. Create Scheduled Job Runner

Create `backend/services/scheduler.py`:

```python
"""APScheduler integration for recurring scraper jobs"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import logging

logger = logging.getLogger(__name__)

class ScraperScheduler:
    """Manages scheduled scraper execution"""

    def __init__(self):
        self.scheduler = BackgroundScheduler()

    def start(self):
        """Start scheduler"""
        self.scheduler.start()
        logger.info("Scraper scheduler started")

    def stop(self):
        """Stop scheduler"""
        self.scheduler.shutdown()
        logger.info("Scraper scheduler stopped")

    def add_scraper_job(
        self,
        scraper_class,
        dispensary_id: str,
        minutes: int = 120
    ):
        """Schedule a scraper to run every N minutes (default: 120 = 2 hours)"""
        self.scheduler.add_job(
            func=scraper_class(dispensary_id).run,
            trigger=IntervalTrigger(minutes=minutes),
            id=f"scraper_{dispensary_id}",
            name=f"Scraper for {dispensary_id}",
            replace_existing=True
        )
        logger.info(f"Scheduled scraper for {dispensary_id} every {minutes} minutes")
```

### 10. Add Error Logging and Retry Logic

Update BaseScraper with retry logic:

```python
# In BaseScraper
import asyncio

async def run_with_retries(self, max_retries: int = 3) -> Dict:
    """Execute scrape with retry logic"""
    for attempt in range(max_retries):
        try:
            return await self.run()
        except Exception as e:
            self.logger.warning(f"Attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(5 * (attempt + 1))  # Exponential backoff
            else:
                return {"status": "error", "error": str(e), "attempts": max_retries}
```

### 11. Test Scraper End-to-End

Create `backend/tests/test_wholesome_scraper.py`:

```python
import pytest
from backend.services.scrapers.wholesome_co_scraper import WholesomeCoScraper

@pytest.mark.asyncio
async def test_scrape_products():
    scraper = WholesomeCoScraper("wholesome-co-id")
    products = await scraper.scrape_products()
    assert len(products) > 0
    assert products[0].name is not None
    assert products[0].price > 0

@pytest.mark.asyncio
async def test_scrape_promotions():
    scraper = WholesomeCoScraper("wholesome-co-id")
    promotions = await scraper.scrape_promotions()
    assert all(p.title for p in promotions)
```

Run tests: `pytest backend/tests/test_wholesome_scraper.py -v`

### 12. Document Scraper API

Add to `backend/README.md`:

```markdown
## Scraper Configuration

Each scraper implements BaseScraper and must provide:
- `scrape_products()` - Returns list of current inventory
- `scrape_promotions()` - Returns list of current promotions

### Running Scrapers

Manually:
```python
from backend.services.scrapers.wholesome_co_scraper import WholesomeCoScraper
scraper = WholesomeCoScraper("dispensary-id")
result = await scraper.run()
```

Scheduled:
```python
from backend.services.scheduler import ScraperScheduler
scheduler = ScraperScheduler()
scheduler.add_scraper_job(WholesomeCoScraper, "dispensary-id", minutes=120)
scheduler.start()
```
```

## Success Criteria

- [ ] BaseScraper abstract class created
- [ ] Fuzzy matching library scores matches correctly
- [ ] Confidence scoring system implemented (>90%/60-90%/<60%)
- [ ] ScraperFlag workflow operational
- [ ] WholesomeCo scraper functional
- [ ] Price history tracked on updates
- [ ] Promotion scraping working
- [ ] APScheduler integration complete
- [ ] Retry logic with exponential backoff
- [ ] Tests passing for scraper
- [ ] >80% auto-merge rate achieved
- [ ] <2 hour refresh cycle maintained
