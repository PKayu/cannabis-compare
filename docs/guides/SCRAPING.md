# Real Data Scraping - Quick Start

**How to start scraping actual dispensary data**

---

## Phase Overview

You are here ↓

```
✅ Phase 1: Foundation (Workflows 01-04) - Database, scrapers infrastructure
✅ Phase 2: Portal (Workflows 05-07) - Product search, detail pages
⚠️ Phase 3: Community (Workflows 08-10) - Auth (done), Reviews (pending)
👉 YOU CAN START SCRAPING NOW
```

---

## When to Start Scraping Real Data

### Option 1: Start Now with One Dispensary (Recommended)

**Pros**:
- ✅ Get real data flowing immediately
- ✅ Test your product pages with actual inventory
- ✅ Validate data normalization early
- ✅ Learn scraping patterns on one site first
- ✅ Users can start comparing real prices

**Cons**:
- ⚠️ Only one dispensary initially (limited value)
- ⚠️ May need to refactor based on learnings

**Best for**: Getting to market faster, validating your system works

### Option 2: Wait Until After Phase 3

**Pros**:
- ✅ Full feature set complete before data ingestion
- ✅ Can test reviews with real products
- ✅ Do all scrapers at once (consistency)

**Cons**:
- ❌ No real data to test with
- ❌ Delays time to market
- ❌ Can't validate assumptions

**Best for**: Perfectionists who want everything ready

---

## Recommended: Start with iHeartJane

**Why iHeartJane first?**

Many Utah dispensaries use iHeartJane's platform:
- WholesomeCo
- Beehive Farmacy
- Dragonfly Wellness
- Others

**Benefits**:
1. **Build once, scrape many**: Same scraper works for all iHeartJane stores
2. **Well-structured API**: They have a JSON API (easier than HTML scraping)
3. **Consistent data**: Product names, prices, THC % formatted consistently
4. **High success rate**: 90%+ auto-merge rate expected

---

## Step-by-Step: Scrape Your First Dispensary

### Step 1: Inspect the Website (15 minutes)

1. **Visit WholesomeCo** (or any dispensary):
   ```
   https://www.wholesomeco.com
   ```

2. **Open DevTools** (F12):
   - Go to Network tab
   - Navigate to their menu/products page
   - Look for API calls (filter by "Fetch/XHR")

3. **Find the data source**:
   - Look for JSON responses with product data
   - Note the API endpoint URL
   - Check authentication (do they need API keys?)
   - Example: `https://api.iheartjane.com/v1/stores/123/products`

4. **Analyze the response**:
   ```json
   {
     "products": [
       {
         "id": "abc123",
         "name": "Blue Dream - 3.5g",
         "brand": "Tryke",
         "category": "Flower",
         "thc_percentage": 22.5,
         "price": 45.00
       }
     ]
   }
   ```

5. **Document the structure** in a comment or notes file

---

### Step 2: Customize the Scraper (30 minutes)

Edit `backend/services/scrapers/wholesome_co_scraper.py`:

```python
class WholesomeCoScraper(BaseScraper):
    """Scrapes WholesomeCo via iHeartJane API"""

    # Update with actual endpoints found in Step 1
    BASE_URL = "https://api.iheartjane.com"
    STORE_ID = "123"  # Find this from the API URL
    MENU_ENDPOINT = f"/v1/stores/{STORE_ID}/products"

    async def scrape_products(self) -> List[ScrapedProduct]:
        """Fetch products from iHeartJane API"""
        products = []

        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.BASE_URL}{self.MENU_ENDPOINT}"

                async with session.get(url, headers=self.HEADERS, timeout=self.TIMEOUT) as response:
                    if response.status != 200:
                        logger.error(f"Failed to fetch: {response.status}")
                        return products

                    data = await response.json()

                    # Parse the response based on actual structure
                    for item in data.get("products", []):
                        product = ScrapedProduct(
                            name=item.get("name"),
                            brand=item.get("brand", {}).get("name"),
                            product_type=self._map_category(item.get("category")),
                            thc_percentage=self._parse_thc(item.get("potency_thc")),
                            cbd_percentage=self._parse_cbd(item.get("potency_cbd")),
                            price=float(item.get("price", 0)),
                            unit_size=self._extract_unit_size(item.get("name")),
                            raw_data=item  # Store original for debugging
                        )
                        products.append(product)

                    logger.info(f"Scraped {len(products)} products from WholesomeCo")

        except Exception as e:
            logger.error(f"Error scraping WholesomeCo: {e}")

        return products

    def _map_category(self, category: str) -> str:
        """Map their category to our product_type"""
        mapping = {
            "Flower": "flower",
            "Pre-Rolls": "pre-roll",
            "Concentrates": "concentrate",
            "Edibles": "edible",
            "Vape": "vaporizer",
            "Topicals": "topical",
        }
        return mapping.get(category, "other")

    def _parse_thc(self, potency) -> Optional[float]:
        """Extract THC percentage"""
        if not potency:
            return None
        # Handle different formats: "22.5%", {"value": 22.5}, etc.
        if isinstance(potency, dict):
            return float(potency.get("value", 0))
        if isinstance(potency, str):
            return float(potency.replace("%", ""))
        return float(potency)

    def _extract_unit_size(self, name: str) -> Optional[str]:
        """Extract unit size from product name"""
        # Example: "Blue Dream - 3.5g" → "3.5g"
        match = re.search(r'(\d+\.?\d*)\s*(g|oz|mg)', name, re.IGNORECASE)
        if match:
            return f"{match.group(1)}{match.group(2)}"
        return None
```

---

### Step 3: Test Locally (10 minutes)

Create a test script `backend/test_scraper_live.py`:

```python
"""
Manual test script for scraper - run this locally to verify
"""
import asyncio
from services.scrapers.wholesome_co_scraper import WholesomeCoScraper

async def test_scraper():
    scraper = WholesomeCoScraper()

    print("Scraping WholesomeCo...")
    products = await scraper.scrape_products()

    print(f"\nFound {len(products)} products\n")

    # Show first 5
    for product in products[:5]:
        print(f"- {product.name}")
        print(f"  Brand: {product.brand}")
        print(f"  Type: {product.product_type}")
        print(f"  THC: {product.thc_percentage}%")
        print(f"  Price: ${product.price}")
        print()

if __name__ == "__main__":
    asyncio.run(test_scraper())
```

Run it:
```bash
cd backend
python test_scraper_live.py
```

**Expected output**:
```
Scraping WholesomeCo...
Found 127 products

- Blue Dream - 3.5g
  Brand: Tryke
  Type: flower
  THC: 22.5%
  Price: $45.00

- Gelato - 1g Pre-Roll
  Brand: Dragonfly
  Type: pre-roll
  THC: 19.8%
  Price: $12.00
```

---

### Step 4: Save to Database (15 minutes)

Create `backend/services/scraper_runner.py`:

```python
"""
Service to run scrapers and save results to database
"""
from sqlalchemy.orm import Session
from services.scrapers.wholesome_co_scraper import WholesomeCoScraper
from services.product_matcher import ProductMatcher
from models import Product, Price, Dispensary, Brand
import logging

logger = logging.getLogger(__name__)

class ScraperRunner:
    """Runs scrapers and saves data to database"""

    def __init__(self, db: Session):
        self.db = db

    async def run_wholesomeco(self):
        """Run WholesomeCo scraper and save results"""
        scraper = WholesomeCoScraper()
        products = await scraper.scrape_products()

        logger.info(f"Scraped {len(products)} products")

        # Get or create dispensary
        dispensary = self._get_or_create_dispensary(
            name="WholesomeCo",
            location="Salt Lake City, UT"
        )

        # Process each product
        matcher = ProductMatcher(self.db)
        for scraped in products:
            # Try to match with existing product
            product = matcher.match_or_create(scraped)

            # Create/update price entry
            self._update_price(product, dispensary, scraped.price)

        self.db.commit()
        logger.info("Database updated successfully")

    def _get_or_create_dispensary(self, name: str, location: str) -> Dispensary:
        """Get existing or create new dispensary"""
        dispensary = self.db.query(Dispensary).filter(
            Dispensary.name == name
        ).first()

        if not dispensary:
            dispensary = Dispensary(name=name, location=location)
            self.db.add(dispensary)
            self.db.flush()

        return dispensary

    def _update_price(self, product: Product, dispensary: Dispensary, price: float):
        """Create or update price entry"""
        from models import Price
        from datetime import datetime

        # Check if price exists
        existing = self.db.query(Price).filter(
            Price.product_id == product.id,
            Price.dispensary_id == dispensary.id
        ).first()

        if existing:
            # Update if price changed
            if existing.price != price:
                existing.price = price
                existing.updated_at = datetime.utcnow()
        else:
            # Create new price entry
            new_price = Price(
                product_id=product.id,
                dispensary_id=dispensary.id,
                price=price
            )
            self.db.add(new_price)
```

Test it:
```python
# backend/test_scraper_to_db.py
import asyncio
from database import SessionLocal
from services.scraper_runner import ScraperRunner

async def test():
    db = SessionLocal()
    runner = ScraperRunner(db)

    await runner.run_wholesomeco()

    # Check results
    from models import Product
    count = db.query(Product).count()
    print(f"Total products in database: {count}")

asyncio.run(test())
```

---

### Step 5: Schedule Regular Scraping (20 minutes)

Option A: **Cron Job (Linux/Mac)**

```bash
# Add to crontab (crontab -e)
# Run scraper daily at 2 AM
0 2 * * * cd /path/to/project/backend && python run_scrapers.py
```

Option B: **APScheduler (Cross-platform)**

Create `backend/scheduler.py`:

```python
"""
Scheduler for running scrapers periodically
"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from database import SessionLocal
from services.scraper_runner import ScraperRunner
import logging

logger = logging.getLogger(__name__)

async def run_all_scrapers():
    """Run all configured scrapers"""
    logger.info("Starting scheduled scraper run")

    db = SessionLocal()
    runner = ScraperRunner(db)

    try:
        await runner.run_wholesomeco()
        # Add more scrapers here as you build them
        # await runner.run_beehive_farmacy()
        # await runner.run_dragonfly()

        logger.info("Scraper run completed successfully")
    except Exception as e:
        logger.error(f"Scraper run failed: {e}")
    finally:
        db.close()

def start_scheduler():
    """Start the background scheduler"""
    scheduler = AsyncIOScheduler()

    # Run every day at 2 AM
    scheduler.add_job(run_all_scrapers, 'cron', hour=2)

    # Or run every 6 hours
    # scheduler.add_job(run_all_scrapers, 'interval', hours=6)

    scheduler.start()
    logger.info("Scraper scheduler started")

    return scheduler
```

Add to `backend/main.py`:
```python
from scheduler import start_scheduler

@app.on_event("startup")
async def startup_event():
    """Start background tasks"""
    start_scheduler()
```

Option C: **Manual Command** (During Development)

```bash
# Create backend/run_scrapers.py
import asyncio
from database import SessionLocal
from services.scraper_runner import ScraperRunner

async def main():
    db = SessionLocal()
    runner = ScraperRunner(db)
    await runner.run_wholesomeco()
    db.close()

asyncio.run(main())
```

Run manually:
```bash
cd backend
python run_scrapers.py
```

---

## Legal & Ethical Considerations

### Before You Scrape

1. **Check Terms of Service**:
   - Read the dispensary's ToS
   - Some prohibit automated scraping
   - Respect robots.txt

2. **Rate Limiting**:
   ```python
   # Add delays between requests
   await asyncio.sleep(1)  # 1 second delay
   ```

3. **User Agent**:
   ```python
   HEADERS = {
       "User-Agent": "UtahCannabisAggregator/1.0 (+https://yoursite.com/about)"
   }
   ```

4. **Contact Dispensaries**:
   - Some may provide API access
   - Partnership opportunities
   - Avoid legal issues

5. **Cache Data**:
   - Don't scrape more than once per day
   - Store data locally
   - Reduce server load

---

## Monitoring Scraper Health

### Add Logging

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/scraper.log'),
        logging.StreamHandler()
    ]
)
```

### Track Metrics

```python
# Track scraper success in database
from models import ScraperRun

run = ScraperRun(
    scraper_name="wholesomeco",
    products_found=len(products),
    products_matched=matched_count,
    success=True,
    error_message=None
)
db.add(run)
```

### Set Up Alerts

```python
# Email yourself if scraper fails
if not success:
    send_email(
        to="you@example.com",
        subject="Scraper Failed",
        body=f"WholesomeCo scraper failed: {error}"
    )
```

---

## Next Steps After First Scraper

1. **Validate Data Quality**:
   - Check product matches in admin dashboard
   - Review normalization accuracy
   - Fix edge cases

2. **Add More Scrapers**:
   - Build iHeartJane base scraper (reuse for all iHeartJane stores)
   - Add Beehive Farmacy
   - Add Dragonfly Wellness

3. **Improve Matching**:
   - Tune ProductMatcher thresholds
   - Add manual merge tools
   - Handle variants (different sizes)

4. **Scale Up**:
   - Run all scrapers nightly
   - Monitor for changes
   - Update when sites change

---

## Troubleshooting

### Scraper Returns Empty List

**Check**:
1. Is the URL correct?
2. Did the website structure change?
3. Check network requests in browser DevTools
4. Look for authentication requirements

### Products Not Matching

**Solution**:
- Lower confidence threshold in ProductMatcher
- Check brand names match database
- Add fuzzy matching for name variations

### Scraper Times Out

**Solution**:
- Increase `TIMEOUT` value
- Add retry logic
- Check internet connection

---

## Summary

**Recommended Timeline**:

- **Week 1**: Build one scraper (WholesomeCo/iHeartJane)
- **Week 2**: Test and refine matching
- **Week 3**: Add 2-3 more dispensaries
- **Week 4**: Schedule automation, monitoring

**Expected Results**:
- 100-200 products per dispensary
- 80-90% auto-match rate
- Daily updates
- Price comparison working with real data

---

**Status**: Ready to implement
**Difficulty**: Medium
**Time**: 2-4 hours for first scraper
**Prerequisites**: Testing infrastructure (✅ Complete)

---

Start with one dispensary, get it working, then expand! 🚀
