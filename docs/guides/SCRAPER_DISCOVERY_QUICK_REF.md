# LLM-Assisted Scraper Discovery - Quick Reference

**Time**: 2-4 hours per scraper | **Cost**: $0 (Gemini free tier)

## The Golden Rule

**❌ NEVER trust LLM CSS selectors** - They hallucinate plausible-sounding class names
**✅ ALWAYS verify selectors** manually using browser DevTools

## 5-Phase Workflow

### 1. Run Discovery (15-30 min)

```bash
cd backend
python scripts/discover_dispensary.py \
    --url https://dispensary.com/menu \
    --name "Dispensary Name" \
    --llm gemini \
    --age-gate "button:has-text('21+')" \
    --wait-for ".product" \
    --scroll
```

**Output**: `discovery_output/{name}_field_map.md`

### 2. Find Real Selectors (30-60 min)

```bash
# Search HTML for actual classes
grep -o 'class="[^"]*product[^"]*"' discovery_output/html/dispensary.html | sort | uniq

# Verify LLM selector is hallucinated
grep -c '.product-item-card' discovery_output/html/dispensary.html  # Returns 0? Fake!
```

**Use DevTools**:
1. Open live site → Right-click product → Inspect
2. Note **actual** class name
3. Test: `document.querySelectorAll('.real-class').length`

### 3. Extract LLM Insights (30 min)

**From `{name}_field_map.md`, use**:

✅ **Extraction Patterns** (regex):
```javascript
weight: /(\d+\.?\d*)\s*(g|gr|mg|oz|pack|pk)/i
thc: /(\d+\.?\d*)\s*(MG|%)?\s*THC/i
price: /\$(\d+\.?\d*)/
```

✅ **Edge Cases**:
- "Weight embedded in name, not separate field"
- "THC can be MG or % depending on product type"

✅ **Coverage Estimates**:
- name: 100%, price: 100%, weight: 95%, brand: 80%

❌ **CSS Selectors** (ignore completely):
- ~~`.product-item-card`~~ (hallucinated)
- ~~`.product-item-name`~~ (hallucinated)

### 4. Implement Scraper (60-90 min)

```python
@register_scraper(id="new-dispensary", name="New Dispensary", ...)
class NewDispensaryScraper(PlaywrightScraper):
    url = "https://dispensary.com/menu"

    async def _extract_products(self, page):
        product_data = await page.evaluate("""
            () => {
                const products = [];

                // ✅ VERIFIED: Actual class from DevTools
                const items = document.querySelectorAll('.productListItem');

                items.forEach(el => {
                    // ✅ VERIFIED: Actual selectors
                    const name = el.querySelector('.product-name')?.textContent;

                    // ✅ LLM PATTERN: Regex from field map
                    const weightMatch = name.match(/(\d+\.?\d*)\s*(g|oz|mg)/i);

                    products.push({name, weight: weightMatch?.[0], ...});
                });

                return products;
            }
        """)
```

### 5. Test & Validate (30-45 min)

```python
# Manual test
python -c "
import asyncio, main
from database import SessionLocal
from services.scraper_runner import ScraperRunner

async def test():
    db = SessionLocal()
    result = await ScraperRunner(db, 'manual_test').run_by_id('new-dispensary')
    print(f'Found: {result.products_found}')
    db.close()

asyncio.run(test())
"
```

**Validate**:
- [ ] Product count > 0
- [ ] Extraction rates match field map estimates
- [ ] No major errors in admin dashboard

## Trust Matrix

| LLM Output | Trust Level | Action |
|------------|-------------|--------|
| **CSS Selectors** | 0% ❌ | Ignore - verify manually |
| **Regex Patterns** | 90% ✅ | Use directly, test edge cases |
| **Edge Cases** | 85% ✅ | Reference when implementing |
| **Coverage %** | 80% ✅ | Use as validation checklist |
| **Field Availability** | 90% ✅ | Trust what exists, verify selectors |

## Common Pitfalls

### ❌ Using LLM selectors without testing
```python
# WRONG - LLM hallucinated this
const items = document.querySelectorAll('.product-item-card');  // 0 matches!
```

### ✅ Verifying selectors manually
```python
# CORRECT - Verified in DevTools
const items = document.querySelectorAll('.productListItem');  // 13 matches
```

### ❌ Trusting LLM about class names
```
LLM: "Use .product-item-price-current for prices"
Reality: No such class exists, actual is .productListItem-price
```

### ✅ Using LLM regex patterns
```python
# LLM pattern works great
const weightMatch = text.match(/(\d+\.?\d*)\s*(g|gr|mg|oz)/i);
```

## Quick Commands

```bash
# Find actual product classes
grep -o 'class="[^"]*product[^"]*"' discovery_output/html/{name}.html | sort | uniq

# Count selector occurrences
grep -c 'productListItem' discovery_output/html/{name}.html

# Test selector in browser console
document.querySelectorAll('.selector-here').length

# View field map
cat discovery_output/{name}_field_map.md

# Re-run discovery if site changed
python scripts/discover_dispensary.py --url ... --name "{Name} 2026-03"
```

## Real Example: WholesomeCo

**LLM Said** (❌ Hallucinated):
- Container: `.product-item-card`
- Name: `.product-item-name`
- Price: `.product-item-price-current`
- **Verification**: 0 matches on page

**Manual Inspection Found** (✅ Correct):
- Container: `.productListItem`
- Name: `.productListItem-content h3`
- Price: `.productListItem-price`
- **Verification**: 13 matches

**LLM Got Right** (✅ Useful):
- Weight regex: `(\d+\.?\d*)\s*(g|gr|mg|oz|pack|pk)`
- Edge case: "Weight embedded in product name"
- Coverage: name 100%, price 100%, weight 95%

## Time Savings

| Approach | Time | Accuracy | Cost |
|----------|------|----------|------|
| Fully Manual | 1-2 days | 95-100% | $0 |
| Fully LLM | 30 min | 0% | $0-0.10 |
| **Hybrid** | **2-4 hours** | **95-100%** | **$0** |

## Environment Setup

```bash
# Add to backend/.env.mcp
GEMINI_API_KEY=your-key-here  # Get from: https://makersuite.google.com/app/apikey

# Test
python scripts/discover_dispensary.py --url https://wholesome.co/shop --name "Test" --llm gemini
```

## Full Guide

See [LLM_ASSISTED_SCRAPER_DISCOVERY.md](LLM_ASSISTED_SCRAPER_DISCOVERY.md) for complete workflow with examples and troubleshooting.
