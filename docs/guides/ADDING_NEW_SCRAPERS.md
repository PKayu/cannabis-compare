# Adding New Scrapers - Complete Workflow

This guide documents the standardized process for adding new dispensary scrapers using the Firecrawl discovery framework.

## Overview

**Before you write any code**, use Firecrawl discovery to understand the site structure. This dramatically reduces development time and improves scraper quality.

**Time to add new scraper**: 2-4 hours (vs 1-2 days without discovery)
**Firecrawl cost**: ~10-20 credits per dispensary
**Free tier limit**: 500 credits/month = 25-50 new scrapers

## Prerequisites

1. **Firecrawl API key configured**
   - Key should be in `.env.mcp` file
   - Format: `FIRECRAWL_API_KEY=fc-your-key-here`
   - Get key from: https://firecrawl.dev/app/api-keys

2. **Backend server accessible**
   - Not required to be running, just Python environment
   - Discovery script is standalone

3. **Dispensary menu URL identified**
   - Find the main products/menu page
   - Example: `https://dispensary.com/menu`

4. **Basic understanding of site structure**
   - Does it have an age gate?
   - Does it use infinite scroll?
   - Single page or category-based?

## Step-by-Step Process

### Step 1: Run Discovery

Use the CLI tool to explore the dispensary website:

```bash
cd backend

# Basic discovery (no age gate)
python scripts/discover_dispensary.py \
    --url https://new-dispensary.com/menu \
    --name "New Dispensary"

# With age gate
python scripts/discover_dispensary.py \
    --url https://dispensary.com/menu \
    --name "Dispensary Name" \
    --age-gate "button:has-text('21+')"

# With age gate + infinite scroll
python scripts/discover_dispensary.py \
    --url https://dispensary.com/menu \
    --name "Dispensary Name" \
    --age-gate "button:has-text('I am 21 or older')" \
    --scroll

# With custom wait time (slower sites)
python scripts/discover_dispensary.py \
    --url https://dispensary.com/menu \
    --name "Dispensary Name" \
    --wait 5000  # 5 seconds
```

**Output**: Two files in `discovery_output/`:
- `{dispensary}_discovery.json` - Full product data
- `{dispensary}_field_map.md` - Field extraction guide

**Cost**: ~5-20 Firecrawl credits depending on page complexity

### Step 2: Review Field Map

Open the generated field map and analyze:

```bash
cat backend/discovery_output/new_dispensary_field_map.md
```

**What to look for**:

1. **Critical Fields Coverage** (should be >95%)
   - `name` - Product names
   - `price` - Prices
   - `weight` - Weights/sizes
   - `url` - Direct product links

2. **Optional Fields** (nice to have if >50% coverage)
   - `image_url` - Product images
   - `description` - Product descriptions
   - `batch_number` - Batch/lot numbers
   - `strain_type` - Indica/Sativa/Hybrid

3. **Extraction Patterns**
   - CSS selectors for each field
   - Regex patterns for complex parsing (weight, cannabinoids)
   - Edge cases and special handling

4. **Data Structure**
   - Single page menu vs multi-category
   - Pagination or infinite scroll
   - Product card structure

**Example field map**:
```markdown
# New Dispensary Field Map

| Field | Coverage | Example | Extraction Pattern |
|-------|----------|---------|-------------------|
| name | 100% | "Blue Dream - 3.5g" | Direct extraction |
| price | 100% | 45.99 | Regex: \$?(\d+\.\d+) |
| weight | 95% | "3.5g" | Regex: (\d+\.?\d*)\s*(g|oz) |
| url | 100% | "https://..." | a.product-link href |
| image_url | 89% | "https://cdn..." | img.product-image src |
```

### Step 3: Create Playwright Scraper

Choose the appropriate template based on site structure:

#### Option A: Single-Page Menu (like WholesomeCo)

Create `backend/services/scrapers/{dispensary}_scraper.py`:

```python
"""
{Dispensary Name} Scraper

Scrapes {Dispensary Name} dispensary menu using Playwright.

Site structure:
- Single page menu at {URL}
- Age gate: {yes/no}
- Infinite scroll: {yes/no}
- Products per page: ~{N}

Field map reference: discovery_output/{dispensary}_field_map.md
"""

import logging
from typing import List

from .playwright_scraper import PlaywrightScraper
from .base_scraper import ScrapedProduct
from .registry import register_scraper

logger = logging.getLogger(__name__)


@register_scraper(
    id="{dispensary-id}",
    name="{Dispensary Name}",
    dispensary_name="{Dispensary Name}",
    dispensary_location="{City}, UT",
    schedule_minutes=120,
    description="Playwright scraper for {Dispensary Name}"
)
class {Dispensary}Scraper(PlaywrightScraper):
    """
    Scraper for {Dispensary Name}.

    Uses selectors discovered via Firecrawl exploration.
    See: discovery_output/{dispensary}_field_map.md
    """

    def __init__(self, dispensary_id: str = "{dispensary-id}"):
        super().__init__(
            menu_url="{https://dispensary.com/menu}",
            dispensary_name="{Dispensary Name}",
            dispensary_id=dispensary_id
        )

    async def scrape_products(self) -> List[ScrapedProduct]:
        """Scrape products using Playwright"""
        # Reference field map for selectors and patterns
        # discovery_output/{dispensary}_field_map.md

        # TODO: Implement extraction logic based on field map
        pass
```

#### Option B: Multi-Category Menu (like Curaleaf)

```python
@register_scraper(
    id="{dispensary-id}",
    name="{Dispensary Name}",
    dispensary_name="{Dispensary Name}",
    dispensary_location="{City}, UT",
    schedule_minutes=120
)
class {Dispensary}Scraper(PlaywrightScraper):
    """Multi-category scraper for {Dispensary Name}"""

    # Categories discovered from field map analysis
    CATEGORIES = ["flower", "vaporizers", "edibles", "concentrates", "tinctures"]

    def __init__(self, dispensary_id: str = "{dispensary-id}"):
        super().__init__(
            menu_url="{https://dispensary.com/menu}",
            dispensary_name="{Dispensary Name}",
            dispensary_id=dispensary_id
        )

    async def scrape_products(self) -> List[ScrapedProduct]:
        """Scrape all categories"""
        all_products = []

        for category in self.CATEGORIES:
            category_url = f"{self.menu_url}/{category}"
            logger.info(f"Scraping {category} from {category_url}")

            # Scrape category page
            # Use selectors from field map
            # ...

        return all_products
```

### Step 4: Implement Extraction Logic

Use selectors and patterns from the field map:

```python
async def scrape_products(self) -> List[ScrapedProduct]:
    """
    Extract products using field map selectors.

    Reference: discovery_output/{dispensary}_field_map.md
    """
    products = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=self.headless)
        page = await browser.new_page()

        try:
            # Navigate to menu
            await page.goto(self.menu_url, wait_until="domcontentloaded")

            # Handle age gate (if needed)
            await self._dismiss_age_gate(page)

            # Load all products (if infinite scroll)
            await self._load_all_products(page)

            # Extract products using selectors from field map
            # Field map says: "Product container: .product-item"
            items = await page.query_selector_all(".product-item")

            logger.info(f"Found {len(items)} product items")

            for item in items:
                try:
                    # Extract fields using patterns from field map
                    # Field map says: "Name: .product-name"
                    name_el = await item.query_selector(".product-name")
                    name = await name_el.inner_text() if name_el else None

                    # Field map says: "Price: .price, Pattern: \$?(\d+\.\d+)"
                    price_el = await item.query_selector(".price")
                    price_text = await price_el.inner_text() if price_el else ""
                    price_match = re.search(r'\$?(\d+\.\d+)', price_text)
                    price = float(price_match.group(1)) if price_match else 0.0

                    # Field map says: "Weight: Pattern: (\d+\.?\d*)\s*(g|oz)"
                    weight_match = re.search(r'(\d+\.?\d*)\s*(g|oz|mg)', name)
                    weight = f"{weight_match.group(1)}{weight_match.group(2)}" if weight_match else None

                    # Field map says: "URL: a.product-link href"
                    link_el = await item.query_selector("a.product-link")
                    url = await link_el.get_attribute("href") if link_el else None

                    # Field map says: "Image: img.product-image src"
                    img_el = await item.query_selector("img.product-image")
                    image_url = await img_el.get_attribute("src") if img_el else None

                    # Create ScrapedProduct
                    product = ScrapedProduct(
                        name=name,
                        brand=None,  # TODO: Extract if available
                        category=self._map_category("flower"),  # TODO: Detect from page
                        price=price,
                        weight=weight,
                        url=url,
                        thc_percentage=None,  # TODO: Extract if available
                        cbd_percentage=None,
                        in_stock=True,  # TODO: Detect from page
                        raw_data={}
                    )
                    products.append(product)

                except Exception as e:
                    logger.warning(f"Error extracting product: {e}")
                    continue

        finally:
            await browser.close()

    logger.info(f"Scraped {len(products)} products from {self.dispensary_name}")
    return products
```

**Key Principles**:
1. **Use exact selectors from field map** - Don't guess
2. **Handle missing data gracefully** - Use `if element else None`
3. **Log warnings, don't crash** - Wrap extraction in try/except
4. **Preserve raw data** - Store in `raw_data` for debugging
5. **Test incrementally** - Run scraper after each field is added

### Step 5: Register Scraper

Add import to `backend/main.py` to trigger registration:

```python
# In backend/main.py
# Add with other scraper imports:
from services.scrapers.new_dispensary_scraper import NewDispensaryScraper  # noqa
```

The `@register_scraper` decorator automatically registers it with the system.

### Step 6: Test via Admin Dashboard

1. **Start backend** (if not already running):
   ```bash
   cd backend
   python -m uvicorn main:app --reload
   ```

2. **Navigate to admin scrapers page**:
   http://localhost:4002/admin/scrapers

3. **Find your new scraper** in the list

4. **Click "Run Now"** to trigger manual run

5. **Wait for completion** (check status)

6. **Verify results**:
   - ✅ Product count > 0
   - ✅ Critical fields populated (name, price, weight, URL)
   - ✅ Low flagging rate (<20% of products flagged for review)
   - ✅ Execution time reasonable (<5 minutes)

7. **Check cleanup queue** (if products flagged):
   http://localhost:4002/admin/cleanup
   - Review flagged products
   - Check if matching/weight parsing needs improvement

### Step 7: Monitor First Runs

Watch the first 2-3 scheduled runs (every 2 hours) for issues:

1. **Check ScraperRun history**:
   - Admin dashboard shows run history
   - Look for consistent success rate

2. **Review flagged products**:
   - Cleanup queue shows products needing review
   - High flagging (>20%) suggests extraction issues

3. **Adjust extraction logic if needed**:
   - Improve weight parsing
   - Fix category detection
   - Handle edge cases

4. **Document any quirks** in scraper docstring:
   ```python
   """
   Scraper for New Dispensary.

   Notes:
   - Weight is embedded in product name, not separate field
   - Some products lack brand data (manufacturer not listed)
   - Out-of-stock items have CSS class '.sold-out'
   """
   ```

## Troubleshooting

### Issue: No Products Found

**Symptoms**:
- `products_found: 0` in scraper run
- Empty products list

**Possible Causes**:
1. **Wrong URL**: Not the products page
2. **Age gate not dismissed**: Products hidden
3. **Slow page load**: Products not rendered yet
4. **Infinite scroll not triggered**: Products lazy-loaded
5. **Selectors don't match**: Field map selectors incorrect

**Solutions**:
```bash
# Re-run discovery with more wait time
python scripts/discover_dispensary.py \
    --url https://dispensary.com/menu \
    --name "Dispensary" \
    --wait 10000  # 10 seconds

# Enable scroll
python scripts/discover_dispensary.py \
    --url https://dispensary.com/menu \
    --name "Dispensary" \
    --scroll

# Check age gate selector
python scripts/discover_dispensary.py \
    --url https://dispensary.com/menu \
    --name "Dispensary" \
    --age-gate ".age-gate-button"  # Try different selector
```

### Issue: High Flagging Rate (>20%)

**Symptoms**:
- Many products in cleanup queue
- Low confidence matches (60-90%)

**Possible Causes**:
1. **Weight not extracted**: Variant matching fails
2. **Brand incorrect**: Fuzzy matching confused
3. **Category wrong**: Products grouped incorrectly

**Solutions**:
1. **Improve weight extraction**:
   ```python
   # Use pattern from field map
   weight_pattern = r'(\d+\.?\d*)\s*(g|oz|mg)'  # From field map
   weight_match = re.search(weight_pattern, product_name)
   weight = f"{match.group(1)}{match.group(2)}" if match else None
   ```

2. **Verify brand extraction**:
   ```python
   # Check field map for brand selector
   brand_el = await item.query_selector(".brand-name")  # From field map
   brand = await brand_el.inner_text() if brand_el else "Unknown"
   ```

3. **Fix category mapping**:
   ```python
   # Use category from field map
   category_text = await item.query_selector(".category")
   category = self._map_category(category_text)  # Normalize
   ```

### Issue: Missing URLs

**Symptoms**:
- Products have no `url` field
- Can't link to product pages

**Solutions**:
1. **Check field map for URL selector**:
   ```python
   # Field map says: "URL: a.product-link href"
   link = await item.query_selector("a.product-link")
   url = await link.get_attribute("href") if link else None
   ```

2. **Construct URL from product ID** (if not available):
   ```python
   # Extract product ID from page
   product_id = await item.get_attribute("data-product-id")
   url = f"https://dispensary.com/products/{product_id}" if product_id else None
   ```

3. **Use relative URL resolution**:
   ```python
   from urllib.parse import urljoin
   url = urljoin(self.menu_url, relative_url)
   ```

### Issue: Slow Scraper (>5 minutes)

**Possible Causes**:
1. **Too many page loads**: Multi-category without batching
2. **Long waits**: Excessive timeout values
3. **No product count check**: Infinite scroll loops forever

**Solutions**:
1. **Batch category scraping** (if multi-category):
   ```python
   # Instead of loading browser for each category,
   # navigate between categories in same browser instance
   ```

2. **Reduce wait times**:
   ```python
   await page.wait_for_selector(".products", timeout=5000)  # Not 30000
   ```

3. **Add scroll safety limit**:
   ```python
   max_scrolls = 50  # Prevent infinite loops
   ```

## Cost Tracking

### Discovery Costs

Each discovery run uses ~10-20 Firecrawl credits:
- Simple page: ~5-10 credits
- Complex page with scroll: ~10-20 credits

**Free tier**: 500 credits/month
**Capacity**: 25-50 new scrapers per month

Monitor usage at: https://firecrawl.dev/dashboard

### When to Re-run Discovery

Re-run discovery when:
1. **Scraper starts failing**: Site redesign changed structure
2. **Adding more fields**: Want to capture new data (images, descriptions)
3. **Monthly audit**: Proactive monitoring for site changes (optional)

Compare old vs new field maps to detect changes:
```bash
diff discovery_output/dispensary_field_map_old.md \
     discovery_output/dispensary_field_map_new.md
```

## Best Practices

### 1. Always Use Discovery First

**Don't skip discovery** even if site looks simple. LLM extraction often finds fields you'd miss manually.

### 2. Keep Field Maps

Don't delete `*_field_map.md` files. They're valuable documentation for:
- Understanding scraper logic
- Debugging scraper failures
- Onboarding new developers

### 3. Test Incrementally

Add fields one at a time, test after each addition:
```python
# First iteration: Just name and price
product = ScrapedProduct(name=name, price=price, ...)

# Test, verify works

# Second iteration: Add weight
product = ScrapedProduct(name=name, price=price, weight=weight, ...)

# Test, verify works

# ... and so on
```

### 4. Handle Edge Cases

Real dispensary sites have messy data:
- Missing fields
- Inconsistent formats
- Special characters
- Out-of-stock items

**Always wrap extraction in try/except**:
```python
try:
    price = float(price_text)
except ValueError:
    logger.warning(f"Invalid price: {price_text}")
    price = 0.0
```

### 5. Document Quirks

If the site has unusual behavior, document it:
```python
"""
Notes:
- Weight sometimes uses fractions (1/8 oz) instead of decimals
- Brand is only shown on hover (need to trigger :hover state)
- Out-of-stock products still appear but have CSS class .unavailable
"""
```

## Common Pitfalls & Lessons Learned

### 1. SQLAlchemy Operator Errors

**Problem**: Using Python comparison operators (`==`, `!=`) with `None`, `True`, or `False` in SQLAlchemy filter clauses causes runtime errors.

**Error Message**:
```
Only '=', '!=', 'is_()', 'is_not()', 'is_distinct_from()', 'is_not_distinct_from()'
operators can be used with None/True/False
```

**Wrong**:
```python
# ❌ This will fail
products = db.query(Product).filter(Product.is_master == True).all()
brands = db.query(Brand).filter(Brand.name.ilike(brand_name)).first()  # Fails if brand_name is None
```

**Correct**:
```python
# ✅ Use .is_() and .is_not() methods
products = db.query(Product).filter(Product.is_master.is_(True)).all()
variants = db.query(Product).filter(Product.is_master.is_(False)).all()
nulls = db.query(Product).filter(Product.weight_grams.is_(None)).all()

# ✅ Handle None values before ilike/like operations
if not brand_name:
    brand_name = "Unknown"
brands = db.query(Brand).filter(Brand.name.ilike(brand_name)).first()
```

**Where This Matters**:
- Any filter clause in normalization code
- Product matching queries
- Brand lookup operations
- Anywhere you query with boolean columns or nullable fields

### 2. Complete ScrapedProduct Field Population

**Problem**: Forgetting to populate new fields throughout the entire data pipeline causes silent data loss.

**Example**: When CBG support was added, the field existed on `ScrapedProduct` but wasn't being passed to variant/parent creation, resulting in 0% CBG coverage despite successful extraction.

**Checklist** for adding new cannabinoid fields (CBG, CBN, etc.):

1. **Add to ScrapedProduct dataclass** ([base_scraper.py](../../backend/services/scrapers/base_scraper.py)):
   ```python
   @dataclass
   class ScrapedProduct:
       cbg_percentage: Optional[float] = None  # ADD THIS
   ```

2. **Add to Product model** ([models.py](../../backend/models.py)):
   ```python
   class Product(Base):
       cbg_percentage: Optional[float] = Column(Float, nullable=True)  # ADD THIS
   ```

3. **Add to variant creation** ([scorer.py](../../backend/services/normalization/scorer.py)):
   ```python
   variant = Product(
       thc_percentage=scraped.thc_percentage or parent.thc_percentage,
       cbd_percentage=scraped.cbd_percentage or parent.cbd_percentage,
       cbg_percentage=scraped.cbg_percentage or parent.cbg_percentage,  # ADD THIS
   )
   ```

4. **Add to parent creation** ([scorer.py](../../backend/services/normalization/scorer.py)):
   ```python
   parent = Product(
       thc_percentage=scraped_product.thc_percentage,
       cbd_percentage=scraped_product.cbd_percentage,
       cbg_percentage=scraped_product.cbg_percentage,  # ADD THIS
   )
   ```

5. **Extract in scraper JavaScript**:
   ```javascript
   // Add CBG pattern to extraction
   let cbgMatch = attrsText.match(/(\d+\.?\d*)%\s*CBG/i);
   if (cbgMatch) cbg = cbgMatch[1];
   ```

6. **Pass to ScrapedProduct creation**:
   ```python
   product = ScrapedProduct(
       thc_percentage=float(item["thc"]) if item.get("thc") else None,
       cbd_percentage=float(item["cbd"]) if item.get("cbd") else None,
       cbg_percentage=float(item["cbg"]) if item.get("cbg") else None,  # ADD THIS
   )
   ```

7. **Create database migration**:
   ```bash
   cd backend
   alembic revision --autogenerate -m "add cbg_percentage to products"
   alembic upgrade head
   ```

**Validation**: After implementation, verify extraction with:
```python
from database import SessionLocal
from models import Product

db = SessionLocal()
total = db.query(Product).count()
with_cbg = db.query(Product).filter(Product.cbg_percentage.is_not(None)).count()
print(f"CBG Coverage: {(with_cbg/total*100):.1f}% ({with_cbg}/{total})")
```

### 3. Handling Non-Product Items

**Problem**: Dispensary websites often have promotional cards, banners, or other elements that match product selectors but aren't actual products.

**Example**: WholesomeCo has "Refer a friend" promo cards that match `.productListItem` selector but have no price, weight, or brand.

**Solutions**:

**Option A: Filter in JavaScript** (preferred for obvious non-products):
```javascript
// Skip promotional cards
const href = await el.getAttribute('href');
if (href && href.includes('/blog/')) continue;  // Promo links to blog
if (href && href.includes('/app/')) continue;   // App download promo

// Skip items without required fields
const nameEl = await el.querySelector('.productName');
const priceEl = await el.querySelector('.price');
if (!nameEl || !priceEl) continue;  // Not a real product
```

**Option B: Graceful Python handling** (for edge cases):
```python
# In scraper_runner.py exception handling
try:
    product_id, action = ConfidenceScorer.process_scraped_product(...)
except Exception as e:
    logger.error(f"Failed to process product '{scraped.name}': {e}", exc_info=True)
    # Don't rollback - ConfidenceScorer uses flush() not commit()
    # Rolling back would lose ALL previous work in this scraper run
    continue
```

**Important**: Never call `db.rollback()` inside the product processing loop. The `ConfidenceScorer` uses `db.flush()` for incremental saves, and rolling back destroys all previous work in the scraper run.

### 4. Brand Name Handling

**Problem**: Some products don't have brand information, causing ilike() errors when brand_name is None.

**Solution**: Always provide a default brand for brandless products:

```python
@staticmethod
def _get_or_create_brand(db: Session, brand_name: str) -> str:
    """Get existing brand or create new one."""
    from models import Brand

    # Handle None or empty brand name
    if not brand_name:
        brand_name = "Unknown"  # ✅ Default for brandless products

    brand = db.query(Brand).filter(Brand.name.ilike(brand_name)).first()
    if not brand:
        brand = Brand(name=brand_name)
        db.add(brand)
        db.flush()
    return brand.id
```

In scraper:
```python
product = ScrapedProduct(
    name=name,
    brand=brand_name or "Unknown",  # ✅ Provide default
    # ... other fields
)
```

### 5. Dual-Format Cannabinoid Extraction

**Problem**: Cannabinoids appear in different formats on the same site:
- Flower/vapes: `"19% THC"` (percentage)
- Edibles: `"100 MG THC"` (milligrams)
- Missing units: `"153 CBG"` (should be mg)

**Solution**: Use multiple regex patterns with fallbacks:

```javascript
// Extract THC - support both percentage and milligram formats
let thc = null;
let thcMatch = attrsText.match(/(\d+\.?\d*)%\s*THC/i);  // Try percentage first
if (thcMatch) {
    thc = thcMatch[1];
} else {
    thcMatch = attrsText.match(/(\d+\.?\d*)\s*(?:mg\s+)?THC/i);  // Fallback to mg (optional unit)
    if (thcMatch) thc = thcMatch[1];
}

// CBG: Percentage or milligram (handle missing "mg" unit)
let cbgMatch = attrsText.match(/(\d+\.?\d*)%\s*CBG/i);
if (cbgMatch) {
    cbg = cbgMatch[1];
} else {
    // Some products show "153 CBG" instead of "153 mg CBG"
    cbgMatch = attrsText.match(/(\d+\.?\d*)\s*(?:mg\s+)?CBG/i);
    if (cbgMatch) cbg = cbgMatch[1];
}
```

**Validation Filter**: Add post-extraction validation to reject impossible values:
```python
# Validate cannabinoid percentages
if thc_percentage and thc_percentage > 100:
    logger.warning(f"Invalid THC value {thc_percentage}% for {name}, setting to None")
    thc_percentage = None
```

### 6. Strain Type from Accessibility Labels

**Problem**: Strain type badges often show only a single letter ("H", "I", "S") but the full name is in the `aria-label`.

**Wrong**:
```javascript
// ❌ Extracts just the letter
const strainMatch = attrsText.match(/\b([HSI])\b/);
if (strainMatch) strainType = strainMatch[1];  // Result: "H"
```

**Correct**:
```javascript
// ✅ Extract full name from aria-label
const strainBadge = el.querySelector('span[aria-label*="ativa"], span[aria-label*="ndica"], span[aria-label*="ybrid"]');
if (strainBadge) {
    const ariaLabel = strainBadge.getAttribute('aria-label');
    if (ariaLabel) {
        strainType = ariaLabel.trim();  // Result: "Hybrid", "Indica", "Sativa"
    }
}
```

**Why This Matters**: Full strain names are more user-friendly and searchable in the frontend.

### 7. Testing Strategy

**Test After Each Change**:
```bash
# 1. Clear existing data
cd backend
python scripts/clear_scraped_data.py

# 2. Run scraper
python -c "
import asyncio
from database import SessionLocal
from services.scraper_runner import ScraperRunner

async def test():
    db = SessionLocal()
    runner = ScraperRunner(db, triggered_by='test')
    result = await runner.run_by_id('wholesomeco')
    print(f'Status: {result[\"status\"]}')
    print(f'Products: {result[\"products_processed\"]}')
    db.close()

asyncio.run(test())
"

# 3. Validate extraction
python -c "
from database import SessionLocal
from models import Product

db = SessionLocal()
total = db.query(Product).count()
with_cbg = db.query(Product).filter(Product.cbg_percentage.is_not(None)).count()
print(f'CBG Coverage: {(with_cbg/total*100):.1f}%')
db.close()
"
```

**Expected Coverage** (based on WholesomeCo validation):
- Name: 100%
- Brand: 100%
- Price: 100% (on variants)
- THC: 95-100%
- CBD: 15-25% (not all products have CBD)
- CBG: 70-80% (most products have some CBG)
- URLs: 100%

**Red Flags**:
- 0% on a field that should have data (CBG, strain type)
- High flagging rate (>30% of products flagged for review)
- Transaction rollbacks (all data lost)
- SQL operator errors (filter clause issues)

## Examples

### Example 1: WholesomeCo (Single Page)

```bash
# Discovery
python scripts/discover_dispensary.py \
    --url https://www.wholesome.co/shop \
    --name "WholesomeCo" \
    --age-gate "button:has-text('21 or older')" \
    --scroll

# Field map showed:
# - Product container: .productListItem
# - Name: .productName
# - Price: .price
# - Weight: embedded in name with regex (\d+\.?\d*)\s*(g|oz)
# - URL: a.productLink href

# Scraper implementation:
# See: backend/services/scrapers/playwright_scraper.py
# (WholesomeCoScraper class)
```

### Example 2: Curaleaf (Multi-Category)

```bash
# Discovery
python scripts/discover_dispensary.py \
    --url https://ut.curaleaf.com/stores/curaleaf-ut-lehi \
    --name "Curaleaf Lehi" \
    --age-gate "button:has-text('over 18')"

# Field map showed:
# - Multiple category pages: /products/flower, /products/vaporizers, etc.
# - Product format: Concatenated text (name + brand + price)
# - Need to parse text in order: price → THC → category → brand → name

# Scraper implementation:
# See: backend/services/scrapers/curaleaf_scraper.py
# (CuraleafScraper class with CATEGORIES list)
```

## Further Reading

- [Backend README](../../backend/README.md) - Scraper architecture
- [CLAUDE.md](../../CLAUDE.md) - Project overview
- [Discovery Output README](../../backend/discovery_output/README.md) - Field map details
- [Firecrawl Documentation](https://docs.firecrawl.dev/) - API reference

---

**Last Updated**: 2026-02-13
**Framework Version**: 1.0
**Questions?** Check CLAUDE.md for project guidance
