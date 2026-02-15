# Curaleaf Scraper Improvements - Task Checklist

**Last Updated**: 2026-02-14

## Pre-Implementation
- [ ] Verify selectors in browser (visit https://ut.curaleaf.com/stores/curaleaf-ut-lehi/products/flower)
  - [ ] Test `[class*="product-item-list"]` selector
  - [ ] Test `[class*="product-carousel"]` selector
  - [ ] Document actual class names if different

## Code Changes

### _load_all_products() Method
- [ ] Change base wait time from 2000ms to 4000ms
- [ ] Add 5-second double-check after stabilization
- [ ] Update logging messages

### _extract_products() JavaScript
- [ ] Add URL extraction (after line 380)
- [ ] Add CBG extraction with dual-format support
- [ ] Add CBN extraction for raw_data
- [ ] Add stock quantity detection ("Only X left")
- [ ] Update product object to include: url, cbg, cbn, stockStatus, stockQuantity

### ScrapedProduct Creation
- [ ] Add `cbg_percentage=self._parse_float(item.get("cbg"))`
- [ ] Add `url=item.get("url")`
- [ ] Ensure CBN is in raw_data

## Testing
- [ ] Run manual scraper test via admin dashboard
- [ ] Verify product count increased (better lazy loading)
- [ ] Verify URLs are populated
- [ ] Verify CBG data is extracted
- [ ] Check database for Price records with product_url
- [ ] Check database for Products with cbg_percentage

## Validation
- [ ] No scraper errors in logs
- [ ] Extraction rates ~95%+ for core fields
- [ ] All three location scrapers working (lehi, provo, springville)
