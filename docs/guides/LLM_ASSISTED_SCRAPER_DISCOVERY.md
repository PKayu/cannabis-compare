# LLM-Assisted Scraper Discovery - Hybrid Workflow

**Status**: Recommended approach for adding new dispensary scrapers
**Last Updated**: 2026-02-14
**Estimated Time**: 2-4 hours per dispensary (vs 1-2 days fully manual)

## Overview

This guide describes the **hybrid workflow** for adding new dispensary scrapers using LLM-assisted discovery combined with manual verification. This approach leverages LLM strengths (pattern recognition, regex generation, structure understanding) while avoiding weaknesses (CSS selector hallucination).

## Key Principle: Trust but Verify

**What LLMs Do Well** ✅:
- Identify what information exists on the page (prices, weights, cannabinoids, brands)
- Suggest regex patterns for text extraction (weight parsing, cannabinoid extraction)
- Recognize data structure patterns (embedded vs separate fields)
- Identify edge cases (missing data, optional fields)
- Estimate field coverage percentages

**What LLMs Do Poorly** ❌:
- Generate CSS selectors (they hallucinate plausible-sounding class names)
- Extract actual class names from HTML (they ignore HTML context)
- Validate that selectors actually exist on the page

## Hybrid Workflow Process

### Phase 1: Automated Discovery (15-30 minutes)

Run the discovery framework to capture page structure and get LLM insights:

```bash
cd backend

# Run discovery with Gemini (free) for initial analysis
python scripts/discover_dispensary.py \
    --url https://new-dispensary.com/menu \
    --name "New Dispensary" \
    --llm gemini \
    --age-gate "button:has-text('21+')" \
    --wait-for ".product" \
    --scroll
```

**Output Files:**
- `discovery_output/screenshots/new_dispensary.png` - Full page screenshot
- `discovery_output/html/new_dispensary.html` - Complete page HTML
- `discovery_output/new_dispensary_field_map.md` - LLM analysis (use with caution)
- `discovery_output/new_dispensary_discovery.json` - Structured data

### Phase 2: Manual Selector Discovery (30-60 minutes)

**Open the captured HTML in a browser or editor and use DevTools:**

1. **Find Product Container:**
   ```bash
   # Search for repeating patterns in the HTML
   grep -o 'class="[^"]*product[^"]*"' discovery_output/html/new_dispensary.html | sort | uniq
   ```

   Example output:
   ```
   class="product-item"
   class="product-card"
   class="productListItem"
   ```

   **Manually verify** which one is the actual container by:
   - Opening browser DevTools on the live site
   - Inspecting a product element
   - Confirming the container class wraps all product info

2. **Find Field Selectors:**

   For each field (name, price, brand, etc.), use DevTools to:
   - Right-click the element → Inspect
   - Note the **actual class name** in the DOM
   - Test the selector in DevTools console:
     ```javascript
     document.querySelectorAll('.actual-class-name').length  // Should match product count
     ```

3. **Document Actual Selectors:**

   Create a verified selector list:
   ```javascript
   // VERIFIED SELECTORS (manually tested)
   container: '.productListItem'  // ✅ 13 elements found
   name: '.productListItem-content h3'  // ✅ Works
   price: '.productListItem-price'  // ✅ Works
   brand: '.productListItem-brand'  // ✅ Works (or null for some)
   ```

### Phase 3: Use LLM Insights Selectively (30-60 minutes)

**Review the LLM-generated field map for useful patterns (ignore selectors!):**

1. **Extraction Patterns** ✅ (Usually reliable):
   ```
   From field map:
   - weight: (\d+\.?\d*)\s*(g|gr|mg|oz|pack|pk)
   - thc: (\d+\.?\d*)\s*(MG|%)?\s*THC
   - price: \$(\d+\.?\d*)
   ```

   **Use these regex patterns directly** - they're typically accurate.

2. **Edge Cases** ✅ (Usually helpful):
   ```
   From field map:
   - "Weight embedded in product name, not separate field"
   - "THC/CBD can be MG (edibles) or % (flower)"
   - "Stock status only shown for low inventory"
   ```

   **These insights save time** - they tell you where to look and what to expect.

3. **Field Coverage** ✅ (Good estimates):
   ```
   From field map:
   - name: 100%
   - price: 100%
   - brand: ~80% (some products lack brand)
   - thc: ~70% (edibles often lack THC%)
   - weight: 100% (embedded in name)
   ```

   **Use as a checklist** when testing your scraper.

4. **CSS Selectors** ❌ (Ignore completely):
   ```
   ❌ DO NOT USE: .product-item-card (hallucinated)
   ❌ DO NOT USE: .productCard-name (hallucinated)
   ❌ DO NOT USE: .product-item-price-current (hallucinated)
   ```

   **Always verify selectors manually** - never trust LLM-generated selectors without testing.

### Phase 4: Implement Scraper (60-90 minutes)

Use the template with your verified selectors and LLM patterns:

```python
from services.scrapers.base_scraper import BaseScraper, ScrapedProduct
from services.scrapers.registry import register_scraper
from playwright.async_api import async_playwright
import re

@register_scraper(
    id="new-dispensary",
    name="New Dispensary",
    dispensary_name="New Dispensary",
    dispensary_location="City, UT",
    schedule_minutes=120,
    description="Playwright-based scraper for New Dispensary"
)
class NewDispensaryScraper(PlaywrightScraper):
    """Scraper for New Dispensary menu."""

    url = "https://new-dispensary.com/menu"
    age_gate_selector = "button:has-text('21+')"
    wait_for_selector = ".productListItem"  # ✅ VERIFIED MANUALLY

    async def _extract_products(self, page):
        """Extract products using VERIFIED selectors + LLM patterns."""

        product_data = await page.evaluate(
            """
            () => {
                const products = [];

                // ✅ VERIFIED: Actual container class from manual inspection
                const productElements = document.querySelectorAll('.productListItem');

                productElements.forEach(el => {
                    try {
                        const fullText = el.textContent || '';

                        // ✅ VERIFIED: Actual name selector from DevTools
                        const nameEl = el.querySelector('.productListItem-content h3');
                        let name = nameEl?.textContent?.trim() || '';

                        // ✅ VERIFIED: Actual price selector from DevTools
                        const priceEl = el.querySelector('.productListItem-price');
                        let price = null;
                        if (priceEl) {
                            // ✅ LLM PATTERN: Use regex from field map
                            const priceMatch = priceEl.textContent.match(/\$(\d+\.?\d*)/);
                            if (priceMatch) price = priceMatch[1];
                        }

                        // ✅ LLM PATTERN: Weight extraction from name (from field map)
                        let weight = null;
                        const weightMatch = fullText.match(/(\d+\.?\d*)\s*(g|gr|mg|oz|pack|pk)/i);
                        if (weightMatch) {
                            weight = weightMatch[1] + weightMatch[2];
                        }

                        // ✅ LLM PATTERN: THC extraction (from field map)
                        let thc = null;
                        const thcMatch = fullText.match(/(\d+\.?\d*)\s*(MG|%)?\s*THC/i);
                        if (thcMatch) thc = thcMatch[1];

                        if (name && price) {
                            products.push({
                                name: name,
                                price: price,
                                weight: weight,
                                thc: thc,
                                // ... other fields
                            });
                        }
                    } catch (e) {
                        console.error('Error parsing product:', e);
                    }
                });

                return products;
            }
            """
        )

        # Convert to ScrapedProduct objects
        products = []
        for item in product_data:
            try:
                product = ScrapedProduct(
                    name=item["name"],
                    category="other",  # Classify later
                    price=float(item["price"]),
                    thc_percentage=float(item["thc"]) if item.get("thc") else None,
                    weight=item.get("weight"),
                    in_stock=True,
                    url=item.get("url"),
                    raw_data=item
                )
                products.append(product)
            except Exception as e:
                logger.warning(f"Failed to parse product: {e}")

        return products
```

### Phase 5: Testing & Validation (30-45 minutes)

1. **Manual Test Run:**
   ```python
   cd backend
   python -c "
   import asyncio
   import main  # Import to register scrapers
   from database import SessionLocal
   from services.scraper_runner import ScraperRunner

   async def test():
       db = SessionLocal()
       runner = ScraperRunner(db, triggered_by='manual_test')
       result = await runner.run_by_id('new-dispensary')
       print(f'Status: {result.status}')
       print(f'Products: {result.products_found}')
       db.close()

   asyncio.run(test())
   "
   ```

2. **Validate Against LLM Coverage Estimates:**
   - Compare actual extraction rates to field map estimates
   - If rates are significantly lower, re-check selectors
   - Verify regex patterns work for edge cases

3. **Admin Dashboard Test:**
   - Navigate to http://localhost:4002/admin/scrapers
   - Manually trigger the new scraper
   - Review flagged items in cleanup queue
   - Check for outlier prices in quality dashboard

## Real-World Example: WholesomeCo Discovery

### What the LLM Said (❌ Hallucinated):

```markdown
## CSS Selectors (from field map)
- container: `.product-item-card`
- name: `.product-item-name`
- brand: `.product-item-brand`
- current_price: `.product-item-price-current`
```

**Verification Result**: 0 matches on actual page - completely hallucinated!

### What Manual Inspection Found (✅ Correct):

```javascript
// ACTUAL selectors from DevTools:
container: '.productListItem'  // 13 matches
name: '.productListItem-content h3'  // Works
brand: '.productListItem-brand'  // Works
price: '.productListItem-price'  // Works
```

### What the LLM Got Right (✅ Useful):

```markdown
## Extraction Patterns
- weight: (\d+\.?\d*)\s*(g|gr|mg|oz|pack|pk)
- thc: (\d+\.?\d*)\s*(MG|%)?\s*THC
- price: \$(\d+\.?\d*)

## Edge Cases
- "Weight embedded in product name, not separate field" ✅
- "THC/CBD can be MG or % depending on product type" ✅
- "Stock status only shown for limited availability" ✅
```

**These insights saved development time** - we knew exactly where to look and how to extract data.

## Checklist for New Scrapers

- [ ] **Phase 1: Run discovery framework**
  - [ ] Capture screenshot and HTML
  - [ ] Generate LLM field map
  - [ ] Save all output files

- [ ] **Phase 2: Manual selector verification**
  - [ ] Open live site in browser
  - [ ] Use DevTools to inspect actual elements
  - [ ] Test selectors in console: `document.querySelectorAll('.selector').length`
  - [ ] Document verified selectors (ignore LLM selectors)

- [ ] **Phase 3: Use LLM insights selectively**
  - [ ] Extract regex patterns from field map ✅
  - [ ] Note edge cases and optional fields ✅
  - [ ] Review coverage estimates ✅
  - [ ] Ignore CSS selectors ❌

- [ ] **Phase 4: Implement scraper**
  - [ ] Use verified selectors (from Phase 2)
  - [ ] Use LLM regex patterns (from Phase 3)
  - [ ] Handle edge cases (from Phase 3)
  - [ ] Test extraction locally

- [ ] **Phase 5: Validate and deploy**
  - [ ] Run manual test
  - [ ] Check extraction rates match estimates
  - [ ] Test via admin dashboard
  - [ ] Review flagged items
  - [ ] Enable scheduler if successful

## Cost Estimation

| Approach | Time | Cost | Accuracy |
|----------|------|------|----------|
| **Fully Manual** | 1-2 days | $0 | 95-100% |
| **Fully Automated (LLM)** | 30 min | $0-0.10 | 0% (hallucinations) |
| **Hybrid (This Guide)** | 2-4 hours | $0 (Gemini free) | 95-100% |

**Recommendation**: Use hybrid approach - best balance of speed and accuracy.

## Troubleshooting

### Problem: LLM selectors don't match any elements

**Solution**: This is expected! Always verify selectors manually using DevTools. The LLM hallucinates class names based on visual appearance.

### Problem: Regex patterns don't capture all variations

**Solution**:
1. Check LLM field map for edge cases
2. Look at flagged items in cleanup queue for patterns
3. Adjust regex to be more permissive
4. Example: `(\d+\.?\d*)` → `(\d+(?:\.\d+)?|\.\d+)` for decimals like ".5g"

### Problem: Extraction rate lower than LLM estimate

**Solution**:
1. Verify selector is correct (use DevTools)
2. Check if field is in a different element than expected
3. Review HTML structure for conditional rendering
4. Consider using broader selector with filtering

### Problem: Discovery finds 0 products after age gate

**Solution**:
1. Check age gate selector syntax (use Playwright format, not jQuery)
2. Increase wait time after dismissal
3. Try `--wait-for` with actual product class from manual inspection
4. Test age gate dismissal in headed mode: remove `headless=True`

## Advanced Tips

### Tip 1: Use HTML Search to Find Selectors

```bash
# Find all classes containing "product"
grep -o 'class="[^"]*product[^"]*"' discovery_output/html/dispensary.html | sort | uniq

# Find all classes containing "price"
grep -o 'class="[^"]*price[^"]*"' discovery_output/html/dispensary.html | sort | uniq

# Count occurrences to identify container vs field
grep -c 'class="productCard"' discovery_output/html/dispensary.html
```

### Tip 2: Test Selectors in Browser Console

```javascript
// Test container selector
document.querySelectorAll('.productCard').length  // Should match product count

// Test extraction logic
document.querySelectorAll('.productCard').forEach(el => {
    const name = el.querySelector('.name')?.textContent;
    const price = el.querySelector('.price')?.textContent;
    console.log({name, price});
});
```

### Tip 3: Use LLM for Pattern Refinement

If LLM regex patterns don't work:

1. Copy examples of actual text from the HTML
2. Ask the LLM: "Generate a regex to extract weight from these examples: ['3.5 g', '1oz', '1000mg']"
3. Test refined regex in Python:
   ```python
   import re
   pattern = r'(\d+\.?\d*)\s*(g|oz|mg)'
   test_cases = ['3.5 g', '1oz', '1000mg', '1/8 oz']
   for case in test_cases:
       match = re.search(pattern, case)
       print(f'{case} -> {match.groups() if match else "NO MATCH"}')
   ```

## Conclusion

The hybrid workflow combines the best of both approaches:

- **LLM strengths**: Pattern recognition, regex generation, structure understanding
- **Manual verification**: Accurate CSS selectors, validation, edge case testing

**Result**: 2-4 hours per scraper with 95-100% accuracy (vs 1-2 days fully manual or 0% accuracy fully automated).

## Related Documentation

- [`ADDING_NEW_SCRAPERS.md`](ADDING_NEW_SCRAPERS.md) - Full scraper development guide
- [`MCP_SETUP_GUIDE.md`](MCP_SETUP_GUIDE.md) - MCP server configuration
- [`../workflows/03_scraper_foundation.md`](../workflows/03_scraper_foundation.md) - Scraper architecture
- [`../../backend/discovery_output/README.md`](../../backend/discovery_output/README.md) - Discovery output reference
