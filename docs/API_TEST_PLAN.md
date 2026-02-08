# Phase 1 API Test Plan

This document provides test cases for all Phase 1 API endpoints with specific parameters and expected results.

## Prerequisites

1. **Server Running**: `uvicorn main:app --reload` from `/backend`
2. **Test Data Seeded**: Run `python seed_test_data.py` from `/backend`
3. **Base URL**: `http://localhost:8000`

## Test Data Summary

| Entity | Count | Key IDs |
|--------|-------|---------|
| Dispensaries | 3 | `disp-001`, `disp-002`, `disp-003` |
| Brands | 4 | `brand-001` through `brand-004` |
| Products (parents) | 6 | `prod-001` through `prod-006` (all have `is_master=True`) |
| Product Variants | varies | e.g., `prod-001-3.5g`, `prod-001-7g` (have `is_master=False`, `master_product_id=prod-001`) |
| Prices | 13 | `price-001` through `price-013` (attached to variant products, not parents) |
| ScraperFlags | 5 | `flag-001` through `flag-005` (4 pending, 1 approved); flags include `original_weight`, `original_price`, `original_category` |
| Users | 2 | `user-001`, `user-002` |
| Reviews | 3 | `review-001` through `review-003` (attached to parent products) |
| Promotions | 3 | `promo-001` through `promo-003` |

### Parent/Variant Structure
- `prod-001` (Blue Dream, parent) has variants like `prod-001-3.5g` (weight="3.5g", weight_grams=3.5)
- Prices are on variant IDs, not parent IDs
- Reviews are on parent IDs, not variant IDs

### Outlier Prices (for testing detection)
- `price-003`: Blue Dream at Beehive Farmacy - $120 (vs ~$46 average) - HIGH severity
- `price-010`: OG Kush Vape at Beehive Farmacy - $5 (vs ~$36 average) - HIGH severity

---

## 1. Health Check

### Test 1.1: Basic Health Check
```bash
curl http://localhost:8000/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "version": "0.1.0"
}
```

---

## 2. Admin Dashboard

### Test 2.1: Get Dashboard Summary
```bash
curl http://localhost:8000/api/admin/dashboard
```

**Expected Response:**
```json
{
  "flags": {
    "pending": 4
  },
  "products": {
    "total_master": 5,
    "total_prices": 13
  },
  "quality": {
    "outliers_total": 2,
    "outliers_high_severity": 2
  }
}
```

---

## 3. Scraper Flags (Cleanup Queue)

### Test 3.1: Get Flag Statistics
```bash
curl http://localhost:8000/api/admin/flags/stats
```

**Expected Response:**
```json
{
  "pending": 4,
  "approved": 1,
  "rejected": 0,
  "total": 5
}
```

### Test 3.2: Get Pending Flags (Default)
```bash
curl http://localhost:8000/api/admin/flags/pending
```

**Expected Response:** Array of 4 pending flags with fields:
- `id`, `original_name`, `brand_name`, `dispensary_id`
- `matched_product_id`, `confidence_score`, `status`

### Test 3.3: Get Pending Flags with Pagination
```bash
curl "http://localhost:8000/api/admin/flags/pending?limit=2&skip=0"
```

**Expected Response:** Array of 2 flags (first page)

```bash
curl "http://localhost:8000/api/admin/flags/pending?limit=2&skip=2"
```

**Expected Response:** Array of 2 flags (second page)

### Test 3.4: Get Pending Flags by Dispensary
```bash
curl "http://localhost:8000/api/admin/flags/pending?dispensary_id=disp-001"
```

**Expected Response:** Array of flags only from WholesomeCo (disp-001)
- Should include: `flag-002` (GG4), `flag-004` (Unknown Strain XYZ)

### Test 3.5: Get Specific Flag Detail
```bash
curl http://localhost:8000/api/admin/flags/flag-001
```

**Expected Response:**
```json
{
  "id": "flag-001",
  "original_name": "Blu Dream",
  "original_thc": 21.5,
  "original_cbd": 0.1,
  "brand_name": "Tryke",
  "dispensary_id": "disp-002",
  "dispensary_name": "Dragonfly Wellness",
  "confidence_score": 0.75,
  "matched_product": {
    "id": "prod-001",
    "name": "Blue Dream",
    "brand": "Tryke",
    "thc_percentage": 22.5,
    "cbd_percentage": 0.1
  },
  "status": "pending",
  "created_at": "..."
}
```

### Test 3.6: Get Non-Existent Flag (Error Case)
```bash
curl http://localhost:8000/api/admin/flags/invalid-id
```

**Expected Response:** HTTP 404
```json
{
  "detail": "Flag not found"
}
```

### Test 3.7: Approve a Flag
```bash
curl -X POST http://localhost:8000/api/admin/flags/approve/flag-001 \
  -H "Content-Type: application/json" \
  -d '{"notes": "Confirmed misspelling of Blue Dream"}'
```

**Expected Response:**
```json
{
  "status": "approved",
  "product_id": "prod-001"
}
```

**Verify:** Run Test 3.1 again - pending count should be 3, approved should be 2

### Test 3.8: Reject a Flag (Create New Product)
```bash
curl -X POST "http://localhost:8000/api/admin/flags/reject/flag-004?product_type=Flower" \
  -H "Content-Type: application/json" \
  -d '{"notes": "This is a new strain not in our database"}'
```

**Expected Response:**
```json
{
  "status": "rejected",
  "new_product_id": "<new-uuid>"
}
```

**Note:** This creates a new product from the flag data

---

## 4. Outlier Detection

### Test 4.1: Get All Outliers
```bash
curl http://localhost:8000/api/admin/outliers
```

**Expected Response:**
```json
{
  "count": 2,
  "outliers": [
    {
      "price_id": "price-003",
      "dispensary_id": "disp-003",
      "amount": 120.0,
      "state_average": 71.0,
      "deviation_percent": 69.01,
      "z_score": 1.41,
      "severity": "medium",
      "product_name": "Blue Dream"
    },
    {
      "price_id": "price-010",
      "dispensary_id": "disp-003",
      "amount": 5.0,
      "state_average": 26.0,
      "deviation_percent": -80.77,
      "z_score": 1.41,
      "severity": "medium",
      "product_name": "OG Kush Vape Cart"
    }
  ]
}
```

### Test 4.2: Get Outliers with Limit
```bash
curl "http://localhost:8000/api/admin/outliers?limit=1"
```

**Expected Response:** Array with only 1 outlier (highest z-score)

---

## 5. Product Management

### Test 5.1: Merge Products
Merge the duplicate "Blue Dream (Alternate)" into the master "Blue Dream":

```bash
curl -X POST http://localhost:8000/api/admin/products/merge \
  -H "Content-Type: application/json" \
  -d '{
    "source_product_id": "prod-006",
    "target_product_id": "prod-001"
  }'
```

**Expected Response:**
```json
{
  "status": "merged",
  "target_id": "prod-001",
  "prices_moved": 0
}
```

**Note:** `prices_moved` is 0 because prod-006 had no prices attached

### Test 5.2: Merge Non-Existent Product (Error Case)
```bash
curl -X POST http://localhost:8000/api/admin/products/merge \
  -H "Content-Type: application/json" \
  -d '{
    "source_product_id": "invalid-id",
    "target_product_id": "prod-001"
  }'
```

**Expected Response:** HTTP 404
```json
{
  "detail": "Source product not found"
}
```

### Test 5.3: Split Product (Create New from Existing)
```bash
curl -X POST http://localhost:8000/api/admin/products/prod-001/split \
  -H "Content-Type: application/json" \
  -d '{
    "product_name": "Blue Dream Premium",
    "brand_id": "brand-001",
    "product_type": "Flower"
  }'
```

**Expected Response:**
```json
{
  "status": "split",
  "new_product_id": "<new-uuid>"
}
```

### Test 5.4: Split with Invalid Brand (Error Case)
```bash
curl -X POST http://localhost:8000/api/admin/products/prod-001/split \
  -H "Content-Type: application/json" \
  -d '{
    "product_name": "Test Product",
    "brand_id": "invalid-brand",
    "product_type": "Flower"
  }'
```

**Expected Response:** HTTP 404
```json
{
  "detail": "Brand not found"
}
```

---

## 6. Query Parameters Reference

| Endpoint | Parameter | Type | Default | Range |
|----------|-----------|------|---------|-------|
| `/flags/pending` | `limit` | int | 50 | 1-100 |
| `/flags/pending` | `skip` | int | 0 | 0+ |
| `/flags/pending` | `dispensary_id` | string | null | - |
| `/outliers` | `limit` | int | 50 | 1-100 |

---

## 7. Testing Workflow

### Recommended Test Sequence

1. **Verify Setup**
   - Run Test 1.1 (Health Check)
   - Run Test 2.1 (Dashboard) - confirms data exists

2. **Explore Data**
   - Run Test 3.1 (Flag Stats)
   - Run Test 3.2 (Pending Flags)
   - Run Test 4.1 (Outliers)

3. **Test Flag Operations**
   - Run Test 3.5 (Get Flag Detail)
   - Run Test 3.7 (Approve Flag)
   - Run Test 3.1 again (Verify count changed)

4. **Test Product Operations**
   - Run Test 5.1 (Merge Products)
   - Run Test 5.3 (Split Product)

5. **Error Cases**
   - Run Test 3.6 (404 on invalid flag)
   - Run Test 5.2 (404 on invalid product)

---

## 8. Browser Testing (Swagger UI)

You can also test all endpoints visually at:
```
http://localhost:8000/docs
```

This provides:
- Interactive API documentation
- Try-it-out functionality for each endpoint
- Request/response examples
- Schema definitions

---

## 9. Resetting Test Data

To clear and re-seed test data:

```bash
cd backend
python seed_test_data.py --clear
# Type "yes" when prompted
python seed_test_data.py
```

---

## 10. Key Test IDs Quick Reference

| Type | ID | Description |
|------|----|-------------|
| Dispensary | `disp-001` | WholesomeCo |
| Dispensary | `disp-002` | Dragonfly Wellness |
| Dispensary | `disp-003` | Beehive Farmacy |
| Brand | `brand-001` | Tryke |
| Brand | `brand-002` | Zion Cultivar |
| Product | `prod-001` | Blue Dream (master) |
| Product | `prod-002` | Gorilla Glue #4 |
| Product | `prod-006` | Blue Dream (duplicate, for merge testing) |
| Flag | `flag-001` | "Blu Dream" - pending (75% match) |
| Flag | `flag-002` | "GG4" - pending (68% match) |
| Flag | `flag-004` | "Unknown Strain XYZ" - no match |
| Flag | `flag-005` | Already approved |
| Price | `price-003` | $120 outlier (Blue Dream) |
| Price | `price-010` | $5 outlier (OG Kush Vape) |

---

## 11. Product Variant Test Cases

### Test 11.1: Grouped Price Response by Weight

Fetch prices for a parent product. Prices should be grouped by variant weight.

```bash
curl http://localhost:8000/api/products/prod-001/prices
```

**Expected Response:** Prices grouped by weight, with each group containing dispensary prices for that weight variant:
```json
{
  "product_id": "prod-001",
  "product_name": "Blue Dream",
  "prices_by_weight": {
    "3.5g": [
      {"dispensary": "WholesomeCo", "price": 45.00, "in_stock": true},
      {"dispensary": "Dragonfly Wellness", "price": 42.00, "in_stock": true}
    ],
    "7g": [
      {"dispensary": "WholesomeCo", "price": 80.00, "in_stock": true}
    ]
  }
}
```

### Test 11.2: Variant-Aware Review Creation

Post a review using a variant product ID. The backend should resolve to the parent product.

```bash
curl -X POST http://localhost:8000/api/reviews \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "product_id": "prod-001-3.5g",
    "rating": 5,
    "comment": "Great flower"
  }'
```

**Expected Behavior:** Review is created with `product_id` set to `prod-001` (the parent), not the variant ID.

### Test 11.3: Search Results with Available Weights

Search results should include `available_weights` for each product.

```bash
curl "http://localhost:8000/api/products/search?q=blue+dream"
```

**Expected Response:** Each result includes aggregated prices across variants and an `available_weights` field:
```json
{
  "results": [
    {
      "id": "prod-001",
      "name": "Blue Dream",
      "available_weights": ["3.5g", "7g", "14g"],
      "lowest_price": 42.00
    }
  ]
}
```

### Test 11.4: Admin Flag Resolution with Variants

Approve a flag. The flag card should show `original_weight`, `original_price`, and `original_category`.

```bash
curl http://localhost:8000/api/admin/flags/flag-001
```

**Expected Response:** Flag detail includes variant context fields:
```json
{
  "id": "flag-001",
  "original_name": "Blu Dream",
  "original_weight": "3.5g",
  "original_price": 45.00,
  "original_category": "flower",
  "confidence_score": 0.75,
  "matched_product": {
    "id": "prod-001",
    "name": "Blue Dream"
  }
}
```

### Test 11.5: Watchlist Variant-to-Parent Resolution

Add a variant to the watchlist. The backend should resolve to the parent product.

```bash
curl -X POST http://localhost:8000/api/watchlist \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"product_id": "prod-001-3.5g"}'
```

**Expected Behavior:** Watchlist entry is created for `prod-001` (the parent product).

### Test 11.6: Dispensary Inventory with Weight Info

Dispensary inventory endpoint should include weight information for products.

```bash
curl http://localhost:8000/api/dispensaries/disp-001/inventory
```

**Expected Response:** Each inventory item includes weight details from the variant:
```json
{
  "inventory": [
    {
      "product_name": "Blue Dream",
      "weight": "3.5g",
      "price": 45.00,
      "in_stock": true
    }
  ]
}
```
