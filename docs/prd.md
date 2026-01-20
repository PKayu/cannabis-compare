# Product Requirements Document: Utah Bud (Working Title)
**Project Name:** Utah Cannabis Aggregator
**Version:** 1.2
**Status:** Draft
**Date:** January 19, 2026

## 1. Executive Summary
Utah Bud is a web-based platform designed specifically for the Utah Medical Cannabis market. It addresses the "Double-Blind" friction point where patients struggle to find the best local prices and lack high-quality, localized feedback on Utah-specific cultivators. The platform aggregates real-time inventory, identifies daily deals, and provides a community-driven review system based on both medical and lifestyle intentions.

## 2. Target Audience
*   **The Budget-Conscious Patient:** Looking for the lowest price point for their specific medication.
*   **The Strain Hunter:** Looking for specific cultivars or terpene profiles across all state pharmacies.
*   **The New Patient:** Seeking community feedback to understand how a specific Utah-grown product affects others.
*   **The Industry Professional:** Budtenders and pharmacists tracking market trends and competitor pricing.

## 3. Success Metrics (KPIs)
*   **Data Freshness:** Inventory and pricing updates at a frequency of <= 2 hours.
*   **Normalization Efficiency:** Achieve a >80% "Auto-Merge" rate for new scraped products.
*   **Review Density:** Average of 3+ reviews per top-tier SKU within 6 months of launch.
*   **User Retention:** % of users returning within a 14-day window (standard refill cycle).

## 4. Functional Requirements

### 4.1. The Price Engine (Core)
*   **Automated Ingestion:** Scrapers for major Utah menu providers (iHeartJane, Dutchie, and proprietary pharmacy APIs).
*   **Confidence-Based Normalization:**
    *   **Auto-Merge (>90% Confidence):** System automatically links products with near-identical names to the "Master Product."
    *   **Flagged for Review (60-90% Confidence):** System creates a "Scraper Flag" for the admin to approve or deny a merge via the dashboard.
    *   **New Product Creation (<60% Confidence):** System defaults to creating a new entry.
*   **Historical Pricing:** Track price fluctuations over time for specific SKUs.

### 4.2. Daily Deals & Promotions
*   **Promo Scraping:** Capture "Specials" banners and "Discounts" sections from dispensary websites.
*   **Recurring Logic:** Support for weekly recurring deals (e.g., "Medical Mondays" or "Friday Vape Sales").
*   **Dynamic Pricing:** Show both the "MSRP" and the "Deal Price" (with the appropriate discount applied) on the product page.

### 4.3. Review System (Quality)
*   **Dual-Track Intention Tags:** Users must select "Why" they used the product.
    *   **Medical:** Pain, Insomnia, Anxiety, Nausea, Spasms.
    *   **Mood/Wellness:** Socializing, Creativity, Deep Relaxation, Focus, Post-Workout.
*   **Standardized Rating:** 1–5 stars for Effects, Taste, and Value.
*   **Batch Tracking:** Users can optionally input a batch number or cultivation date to ensure review relevance.

### 4.4. Admin Dashboard (Data Management)
*   **The "Cleanup" Queue:** A specialized UI to resolve product naming discrepancies.
*   **Merge/Split Actions:** One-click functionality to merge a scraped name into an existing product or split a product into its own entry.
*   **Outlier Alerts:** Flag products where the scraped price is significantly higher/lower than the state average (helps catch scraping errors).

## 5. User Flow: Finding a Deal
1.  **Landing:** User passes the 21+ age gate.
2.  **Search:** User searches for "Zion Fruit de la Passion."
3.  **Product Page:** User sees a comparison table:
    *   Pharmacy A: $45 (In stock)
    *   Pharmacy B: $55 (In stock - Note: 15% off flower today!)
4.  **Filter:** User filters reviews by "Mood: Social" to see if this batch is suitable for daytime use.
5.  **Redirect:** User clicks "Order at Pharmacy B" and is deep-linked to the pharmacy's external checkout.

## 6. Technical Architecture

### 6.1. Tech Stack
*   **Frontend:** Next.js (React) using Tailwind CSS for mobile responsiveness.
*   **Backend:** FastAPI (Python) for robust, asynchronous web scraping.
*   **Database:** PostgreSQL (via Supabase) for relational data integrity.
*   **Authentication:** Supabase Auth (Magic Links and OAuth).

### 6.2. High-Level Data Model
| Table | Description |
| :--- | :--- |
| **Products** | The "Master" entry (Name, Brand, Category). |
| **Dispensaries** | Utah pharmacy details (Location, Hours, Website). |
| **Prices** | Junction table linking Products to Dispensaries with a price and timestamp. |
| **Promotions** | Stores dispensary-wide or category-specific discounts. |
| **Reviews** | User ratings linked to Products and Intention Tags. |
| **ScraperFlags** | Log of "dirty" product names requiring admin normalization. |

## 7. Roadmap
*   **Phase 1: The Foundation**
    *   Build scrapers for the top 3 Utah dispensaries (e.g., WholesomeCo, Dragonfly, Curaleaf).
    *   Implement the initial "Fuzzy Matching" normalization logic.
    *   Build the Admin Dashboard for manual data cleanup.
*   **Phase 2: The Portal**
    *   Launch the frontend "Price Comparison" search engine.
    *   Implement the "Daily Deals" display logic.
*   **Phase 3: The Community**
    *   Enable User Accounts.
    *   Launch the Review System with Intention Tags.
    *   Implement "Stock Alerts" for watched strains.