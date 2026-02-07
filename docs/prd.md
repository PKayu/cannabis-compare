# Product Requirements Document: Utah Cannabis Aggregator
**Project Name:** Utah Cannabis Aggregator
**Version:** 2.0
**Status:** Complete MVP
**Date:** February 3, 2026

## 1. Executive Summary
Utah Cannabis Aggregator is a web-based platform designed specifically for the Utah Medical Cannabis market. It addresses the "Double-Blind" friction point where patients struggle to find the best local prices and lack high-quality, localized feedback on Utah-specific cultivators. The platform aggregates real-time inventory, identifies daily deals, and provides a community-driven review system based on both medical and lifestyle intentions.

**Important:** This is an informational-only platform. The site does not sell or facilitate transactions for controlled substances. All products must be purchased directly from licensed Utah pharmacies. A compliance banner appears on every page reinforcing this requirement.

**Current Status:** All MVP phases complete (January 2026)

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
*   **Automated Ingestion:** Scrapers for major Utah menu providers (WholesomeCo, Curaleaf, iHeartJane integrations).
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
*   **User Attribution:** Reviews are linked to user profiles with timestamps and helpfulness voting.

### 4.4. Notifications & Alerts (Community)
*   **Stock Alerts:** Notify users when out-of-stock products become available.
*   **Price Drop Alerts:** Notify users when prices drop below user-set thresholds.
*   **Email Notification Preferences:** Users control frequency (immediate, daily digest, weekly summary).
*   **24-hour Deduplication:** Prevent duplicate alerts for the same product.
*   **Alert Type Toggles:** Users can enable/disable stock alerts and price drops independently.

### 4.5. Admin Dashboard (Data Management)
*   **Main Dashboard:** Overview metrics including pending flags, scraper health, product count, and price outliers. Quick actions to navigate to all admin sections.
*   **Scraper Management:** Monitor scraper health (7-day success rates), trigger manual runs, view execution history, pause/resume individual scrapers.
*   **Cleanup Queue:** Specialized UI to resolve product naming discrepancies. One-click functionality to merge a scraped name into an existing product or split a product into its own entry.
*   **Data Quality Metrics:**
    *   Data completeness tracking (missing THC%, CBD%, brand information)
    *   Category distribution analysis
    *   Dispensary freshness monitoring (last successful scrape times)
    *   Price outlier detection (statistical analysis for suspicious pricing)

### 4.6. User Accounts & Authentication
*   **Age Verification:** 21+ age gate on first visit with localStorage persistence.
*   **Authentication Methods:** Magic link email authentication and Google OAuth.
*   **User Profiles:** Public profile page showing review history and account details.
*   **Watchlist:** Track products and configure price alerts.
*   **Notification Preferences:** Customizable email frequency and alert type toggles.

## 5. Website Navigation

### Main Navigation Structure

The site uses a clean, mobile-responsive navigation with the following primary sections:

*   **Home** (`/`): Landing page with feature overview and call-to-action
*   **Browse Products** (`/products/search`): Price comparison search with filters for category, price range, THC/CBD potency, and dispensary
*   **Dispensaries** (`/dispensaries`): Browse all Utah dispensaries with locations, hours, and inventory counts
*   **Watchlist** (`/watchlist`): Track products and set alerts (authenticated users only)
*   **Profile** (`/profile`): User account management and review history (authenticated users only)

### Detailed User Flows

#### Flow 1: Finding a Deal (Price Comparison)
1.  User passes 21+ age gate on first visit
2.  Searches for "Zion Fruit de la Passion" via search bar
3.  Views comparison table showing prices across all dispensaries
    *   Pharmacy A: $45 (In stock)
    *   Pharmacy B: $55 (In stock - 15% off flower today!)
    *   Pharmacy C: $50 (Out of stock)
4.  Filters reviews by "Mood: Social" to see if this strain is suitable for daytime use
5.  Clicks "Order at Pharmacy B" to deep-link to the pharmacy's external checkout
6.  Completes purchase directly on the pharmacy's website

#### Flow 2: Setting Up Price Alerts
1.  User searches for a product currently out of stock
2.  Adds product to watchlist (requires authentication)
3.  Sets price threshold alert: "Notify me if price drops below $40/oz"
4.  Selects notification preference: "Immediate" or "Daily digest"
5.  System monitors product availability and pricing
6.  User receives email when product becomes available or price drops

#### Flow 3: Writing a Review
1.  User navigates to a purchased product page
2.  Clicks "Write a Review" button (requires authentication)
3.  Selects intention tags:
    *   Medical: Pain, Insomnia, Anxiety, Nausea, Spasms
    *   Mood/Wellness: Socializing, Creativity, Deep Relaxation, Focus, Post-Workout
4.  Rates three categories (1-5 stars): Effects, Taste, Value
5.  Optionally adds batch number or cultivation date for accuracy
6.  Writes text review describing their experience
7.  Submits review for the community benefit
8.  Review appears on product page with user attribution and timestamp

#### Flow 4: Managing Watchlist
1.  User accesses watchlist from profile or navigation bar
2.  Views all tracked products with current pricing and alert status
3.  Sees indicators for price drops and back-in-stock notifications
4.  Removes products no longer tracking
5.  Adjusts price thresholds for alerts on individual products
6.  Clicks through to product pages to purchase

#### Flow 5: Configuring Notification Preferences
1.  User navigates to Profile → Notifications
2.  Toggles alert types on/off: Stock alerts, Price drops
3.  Selects email frequency: Immediate, Daily digest, Weekly summary
4.  Saves preferences
5.  System sends emails according to user's settings
6.  User can return anytime to adjust preferences

### Authentication Flow

*   **Login:** User clicks "Login" button → Chooses Magic Link (email) or Google OAuth
*   **Registration:** New users complete age verification (21+) during first sign-in
*   **Session Management:** User stays logged in across browser sessions
*   **Profile:** View review history, public profile, and notification preferences
*   **Watchlist:** Track products and configure alerts
*   **Sign Out:** One-click sign out from user menu

### Compliance Features

*   **Age Gate:** 21+ verification on first visit with localStorage persistence
*   **Compliance Banner:** Appears on every page stating the site is informational only and does not sell controlled substances
*   **External Checkout:** All purchases occur on pharmacy websites, not on this platform

## 6. Technical Architecture

### 6.1. Tech Stack
*   **Frontend:** Next.js (React) using Tailwind CSS for mobile responsiveness.
*   **Backend:** FastAPI (Python) for robust, asynchronous web scraping.
*   **Database:** PostgreSQL (via Supabase) for relational data integrity.
*   **Authentication:** Supabase Auth (Magic Links and OAuth).
*   **Email:** SendGrid integration for notifications.

### 6.2. High-Level Data Model
| Table | Description |
| :--- | :--- |
| **Products** | The "Master" entry (Name, Brand, Category, THC/CBD%). |
| **Dispensaries** | Utah pharmacy details (Location, Hours, Website). |
| **Prices** | Junction table linking Products to Dispensaries with a price and timestamp. |
| **Promotions** | Stores dispensary-wide or category-specific discounts. |
| **Reviews** | User ratings linked to Products and Intention Tags. |
| **Users** | User accounts with authentication and notification preferences. |
| **Watchlist** | Products users are tracking for alerts. |
| **PriceAlerts** | User-configured price thresholds. |
| **NotificationPreferences** | Email frequency and alert type settings. |
| **ScraperFlags** | Log of "dirty" product names requiring admin normalization. |
| **ScraperRuns** | Execution history and performance metrics for scrapers. |

## 7. Roadmap

### Phase 1: The Foundation ✅ COMPLETE
*   Built scrapers for top Utah dispensaries (WholesomeCo, Curaleaf).
*   Implemented the initial "Fuzzy Matching" normalization logic.
*   Built the Admin Dashboard for manual data cleanup.
*   Database schema and migrations with Alembic.

### Phase 2: The Portal ✅ COMPLETE
*   Launched the frontend "Price Comparison" search engine.
*   Implemented the "Daily Deals" display logic.
*   Product detail pages with pricing history.
*   Dispensary pages with inventory and promotions.

### Phase 3: The Community ✅ COMPLETE
*   Enabled User Accounts with authentication (Magic Link + Google OAuth).
*   Launched the Review System with Intention Tags.
*   Implemented "Stock Alerts" and "Price Drop Alerts" for watched products.
*   Email notification system with user-configurable preferences.

## 8. Future Enhancements

Potential post-MVP features under consideration:

*   **Mobile App:** Native iOS/Android app for on-the-go price checking
*   **Additional Scrapers:** Expand coverage to more Utah dispensaries
*   **Social Features:** Follow other reviewers, see what friends recommend
*   **Price Analytics:** Historical price charts and trend analysis
*   **Loyalty Integration:** Connect with dispensary loyalty programs
*   **Batch Reviews:** Photos and batch-specific review tracking
*   **Advanced Search:** Filter by terpene profiles, effects-based recommendations
*   **Dispensary Ratings:** Rate pharmacies based on inventory freshness and pricing
*   **Newsletter:** Weekly email digest of deals and price drops
*   **Stash Builder:** Comparison tool to optimize purchases across multiple dispensaries

## 9. Compliance & Legal

*   **Age Requirement:** All users must be 21+ years old
*   **Medical Only:** Target audience is Utah Medical Cannabis Cardholders
*   **Informational Only:** Site does not sell or facilitate transactions
*   **Disclaimer:** Compliance banner on every page reinforcing informational nature
*   **External Purchases:** All transactions occur on licensed pharmacy websites

## 10. Performance Targets

*   **Search Response:** <200ms for product search queries
*   **Page Load:** <2 seconds for initial page load
*   **Mobile Responsiveness:** 80% of users access via mobile (mobile-first design)
*   **Data Freshness:** Scrapers run every 2 hours
*   **Uptime:** >99% availability for price comparison data
