# App Context: CannabisCompare (Utah)

Use this file to form gap-analysis recommendations that are specific and immediately actionable.

---

## Identity & Audience

- **Name**: CannabisCompare (working name)
- **Purpose**: Price comparison and product discovery for Utah Medical Cannabis patients
- **Audience**: Utah MMJ cardholders — patients who are cost-conscious, sometimes new to cannabis, and need to navigate a licensed-only state market
- **Compliance requirement**: Every page must display a disclaimer that this is informational only and does not sell controlled substances
- **Geography**: Utah only (10 licensed dispensaries statewide as of early 2026)
- **Business model**: Free to patients; potential future monetization via dispensary partnerships or advertising

---

## Current Pages & Features

### Public-Facing

| Page | Route | What it does |
|------|-------|-------------|
| Home | `/` | Landing page, likely entry point for new users |
| Product Search | `/products/search` | Fuzzy-match search with filters; returns product cards |
| Product Detail | `/products/[id]` | Shows product info, all variants (weights), price comparison table across dispensaries, user reviews |
| Dispensary List | `/dispensaries` | Lists all Utah dispensaries with basic info |
| Dispensary Detail | `/dispensaries/[id]` | Shows dispensary info, inventory/products available there |
| Login | `/auth/login` | Magic link + Google OAuth via Supabase |
| OAuth Callback | `/auth/callback` | Handles Supabase auth redirect |
| Watchlist | `/watchlist` | Saved products for logged-in users |
| Profile | `/profile` | User account settings |
| Notifications | `/profile/notifications` | Price drop / back-in-stock alert preferences |

### Admin (Internal)

| Page | Route | What it does |
|------|-------|-------------|
| Admin Dashboard | `/admin` | Overview |
| Scraper Management | `/admin/scrapers` | Run, pause, schedule scrapers per dispensary |
| Data Quality | `/admin/quality` | Cross-dispensary duplicate detection, orphan repair |
| Cleanup Dashboard | `/admin/cleanup` | Data hygiene tools |
| Scraper Insights | `/admin/scraper-insights` | Analytics on scraper run history |

---

## Existing Features (Detailed)

### Search & Discovery
- ✅ Fuzzy search (rapidfuzz) across product names
- ✅ Filter by category (flower, edible, concentrate, etc.)
- ✅ Price comparison table: same product across multiple dispensaries side by side
- ✅ Variant selection: view prices for different weights of the same product
- ❌ No strain-type filter (indica / sativa / hybrid)
- ❌ No THC% range filter (even though THC% is stored)
- ❌ No brand filter
- ❌ No "sort by price" or "sort by THC%" on search results
- ❌ No saved search / search history

### Product Data
- ✅ Product name, brand, category, THC%, CBD% stored
- ✅ Weight variants with per-variant pricing
- ✅ Prices scraped from all Utah dispensaries automatically
- ✅ `product_url` links back to source dispensary page
- ❌ No terpene profiles
- ❌ No lab result / COA display
- ❌ No product images (rely on text only)
- ❌ No strain lineage or genetics
- ❌ No effects tags (relaxing, energizing, pain relief, etc.)

### User Features
- ✅ User accounts (magic link + Google OAuth)
- ✅ Watchlist (save products)
- ✅ Price drop alerts (email notifications via SendGrid)
- ✅ Back-in-stock alerts
- ✅ Product reviews (text + rating, upvote system)
- ❌ No user-contributed strain reviews with effects tagging
- ❌ No community Q&A
- ❌ No "recently viewed" products
- ❌ No personalized recommendations
- ❌ No mobile app (web only, but responsive)

### Dispensary Features
- ✅ Dispensary listing with location (Utah)
- ✅ Dispensary inventory browsing
- ❌ No real-time hours or open/closed status
- ❌ No distance/location-based filtering (no map)
- ❌ No deals or promotions page (even though promotions are scraped)
- ❌ No online ordering / reservation integration (complex — dispensaries use different systems)

### Content & SEO
- ❌ No blog or editorial content
- ❌ No strain guide or educational content
- ❌ No "beginner's guide to Utah MMJ" type content
- ❌ URL slugs are ID-based (not keyword-rich)
- ❌ No schema markup (Product, Organization, BreadcrumbList)
- ❌ Meta descriptions likely auto-generated, not hand-crafted

---

## Tech Constraints Relevant to Recommendations

| Constraint | Impact on recommendations |
|------------|--------------------------|
| Next.js 14 App Router | SSR/SSG possible — static pages for SEO-friendly product/dispensary pages are achievable |
| Supabase PostgreSQL | Full-text search available (pg_trgm); could power better search without Algolia |
| No mobile app | PWA features (installable, push notifications) could partially close the gap |
| Utah-only data | Features like "find nearest dispensary" require knowing user location |
| Compliance-first | Any marketing copy must avoid language suggesting purchase or medical advice |
| Scraper-driven data | Data freshness depends on scrape frequency; real-time inventory is not guaranteed |

---

## Priority Focus Areas (as of Feb 2026)

Based on MVP completion status, these areas are most open for improvement:
1. **SEO / organic discoverability** — currently no content strategy
2. **Richer product data** — effects, terpenes, images would significantly improve UX
3. **Deals & promotions** — data is scraped but not surfaced to users
4. **Advanced filtering** — strain type, THC%, brand are high-value filters
5. **Trust & social proof** — reviews exist but aren't prominently featured
