# Competitor Analysis: leafly.com
**Date**: 2026-02-24
**Source URL**: https://www.leafly.com
**Analyzed by**: /market-research skill

---

## Executive Summary

- **Effects & strain-type filtering is Leafly's most powerful discovery tool** — patients can filter by "Relaxed," "Sleepy," "Euphoric" effects or Indica/Sativa/Hybrid at the top of every search; CannabisCompare has none of this despite storing THC% and category data.
- **Product images + rich metadata are table stakes** — every Leafly product card shows brand, strain type, THC/CBD%, price, weight, AND a photo; our text-only cards feel sparse by comparison.
- **Deals/promotions are a high-intent traffic driver** — Leafly surfaces "25% off Select Deli Bud" directly on dispensary cards; we scrape promotions but never show them to users.
- **SEO is built into every URL and title tag** — `/strains/blue-dream`, `/dispensaries/utah`, hand-crafted meta descriptions, and schema markup on every page type drives massive organic traffic; our ID-based URLs and auto-generated meta tags leave this entirely untapped.
- **Dispensary open/closed status and hours are displayed in real time** — patients need to know if a dispensary is open before driving there; our dispensary pages have no hours data.

---

## UX & Design Analysis

### Navigation Structure
Leafly's top nav has 12 top-level categories: Shop, Delivery, Dispensaries, Deals, Strains, Brands, Products, Leafly Picks, CBD, Doctors, Cannabis 101, Social impact. This breadth reflects years of SEO-driven content expansion. For CannabisCompare's focused Utah-only scope, a leaner nav is appropriate — but **Deals, Strains, and Cannabis 101 are worth adding** as dedicated sections.

### Search UX
- Location is set from the first page load and persists globally
- `/shop` search has a 12-dimension filter sidebar: fulfillment type, category, dispensary, rec/med, brand, THC% range (bucketed: None / Low 1-10% / Medium 10-20% / High >20%), THC mg amount, price range, weight amount, strain type, and effects
- Default sort is "Recommended"; users can switch to distance, highest rated, most reviews, A-Z
- Filter counts shown in parentheses next to each option (e.g., "Flower (2091)")
- **Gap**: CannabisCompare has category filter only. Missing: strain type, THC% range, price range, effects, weight, sort options.

### Product Cards
Leafly cards display: product image, brand, name, strain category badge (Indica/Sativa/Hybrid), THC%, CBD%, price, weight/size, distance to dispensary, fulfillment method, and "Add to cart" CTA. This is approximately 4× the data density of our current cards.

### Dispensary Cards
Cards show: logo, name, MED/REC badge, star rating + review count, distance in miles, real-time hours status ("Closed until 11am MT"), active deal count ("3 deals"), and fulfillment options. Our dispensary cards lack hours, deals, and distance entirely.

### Strain Detail Pages
Leafly strain pages are the richest content type: effects percentages (user-reported), flavor profiles, terpene data, medical applications (e.g., "helps with: Stress 36%, Anxiety 31%"), negative effects, genetics/lineage, grow info, 14,000+ user reviews, similar strains carousel, and a direct shop CTA. These pages rank extremely well in Google. We have no equivalent.

### Mobile
Leafly promotes a native app (iOS + Android, 300,000+ reviews). Our app is web-only but Next.js makes PWA feasible as a partial substitute.

### Accessibility
Alt text and ARIA labels visible in the HTML. A dedicated "Accessibility" footer link exists. Low-friction area for us to improve.

---

## Feature Inventory & Gaps

| Feature | Leafly Has | App Has | Priority to Build |
|---------|-----------|---------|------------------|
| Strain type filter (I/S/H) | ✅ | ❌ | 🔴 High |
| THC% range filter | ✅ | ❌ | 🔴 High |
| Effects filter (Relaxed, Sleepy…) | ✅ | ❌ | 🔴 High |
| Product images | ✅ | ❌ | 🔴 High |
| Dispensary open/closed + hours | ✅ | ❌ | 🔴 High |
| Deals / promotions page | ✅ | ❌ (scraped, not surfaced) | 🔴 High |
| Keyword-rich URL slugs | ✅ | ❌ (ID-based) | 🔴 High |
| Schema markup (Product, BreadcrumbList) | ✅ | ❌ | 🔴 High |
| Price range filter | ✅ | ❌ | 🟡 Medium |
| Sort by price / THC% / rating | ✅ | ❌ | 🟡 Medium |
| Brand filter | ✅ | ❌ | 🟡 Medium |
| Terpene profiles | ✅ | ❌ | 🟡 Medium |
| Trust stat display (review counts, etc.) | ✅ | ❌ (reviews exist but not surfaced) | 🟡 Medium |
| Distance-based dispensary sorting | ✅ | ❌ | 🟡 Medium |
| Filter counts per option | ✅ | ❌ | 🟡 Medium |
| Cannabis 101 educational section | ✅ (11,000+ articles) | ❌ | 🟡 Medium |
| Meta descriptions (hand-crafted) | ✅ | ❌ (auto-generated) | 🟡 Medium |
| Newsletter / email capture | ✅ | ❌ | 🟢 Low |
| Strain lineage / genetics | ✅ | ❌ | 🟢 Low |
| Grow information | ✅ | ❌ | 🟢 Low |
| Native mobile app | ✅ (iOS + Android) | ❌ | 🟢 Low (PWA first) |
| Leafly Picks / editorial curation | ✅ | ❌ | 🟢 Low |
| Social impact section | ✅ | ❌ | 🟢 Low |
| Payment method filter | ✅ | ❌ | 🟢 Low |
| Accessibility filter (wheelchair, etc.) | ✅ | ❌ | 🟢 Low |
| Price comparison across dispensaries | ❌ | ✅ | — (our differentiator) |
| Utah-specific scraper data | ❌ | ✅ | — (our differentiator) |
| Watchlist + price alerts | ❌ (basic) | ✅ | — (our differentiator) |

---

## Marketing & Copy Analysis

### Headlines & Value Proposition
- **Hero headline**: "Shop legal, local weed." — Direct, action-oriented, immediately communicates legality (trust). No fluff.
- **Sub-headline**: "A great place to discover cannabis." — Weaker; generic.
- **CannabisCompare opportunity**: Our headline should lead with the patient value prop: price comparison and transparency. Something like "Find the best price on your medication across all Utah dispensaries" would be cleaner than anything generic.

### CTAs
Leafly's above-fold CTAs are task-driven: "order pickup," "see dry herb vape picks," "hit this list." They avoid generic "Learn More" language entirely. Every CTA names a specific action or product category. Our primary CTA on the homepage should be a functional search bar with clear prompt text — not a static hero.

### Trust Signals
Leafly displays social proof metrics prominently in the nav/hero region:
- "11,000+ articles"
- "5,000+ strains"
- "1.3mm+ reviews"

We don't surface any equivalent stats. We have real data (# products tracked, # dispensaries, # price updates/day) that could build similar trust. Displaying "Price data from 10 Utah dispensaries, updated daily" would immediately establish credibility.

### Compliance Messaging
Leafly places the FDA disclaimer at the footer (boilerplate). They use the frame "Shop legal, local weed" to communicate legitimacy in the headline itself — legality is a trust signal, not just a disclaimer. CannabisCompare already has a compliance banner; consider whether its placement and wording is working as a trust signal or just legal cover.

### Tone
Leafly is casual and consumer-friendly: "weed," "hit this list," "get the picks." CannabisCompare targets medical patients — a slightly more clinical/respectful tone is appropriate, but "cannabis medication" language at every touchpoint is unnecessarily stiff. Watch competitor tone for patients who are cost-conscious and practical, not recreational.

### Email Capture
Leafly has a newsletter sign-up ("sign up") appearing twice below the fold. We have no email capture beyond account creation. A simple "Get weekly deals from Utah dispensaries" email could drive direct retention traffic.

---

## SEO & Discoverability Signals

### URL Structure
| Leafly Pattern | CannabisCompare Pattern | Issue |
|---------------|------------------------|-------|
| `/strains/blue-dream` | `/products/[uuid]` | Not indexable by keywords |
| `/dispensaries/utah` | `/dispensaries/[uuid]` | Not indexable by location |
| `/news/cannabis-101` | (no content section) | Missing entirely |

Our ID-based URLs cannot rank for "blue dream Utah" or "best dispensary Salt Lake City" because there's no keyword in the URL. Next.js App Router supports dynamic slug-based routes — this is a direct code change, not a rearchitecture.

### Title Tags
Leafly title examples:
- "Find, order, and learn about weed | Leafly" (homepage)
- "The Best Dispensaries Near Me in Utah | Updated 2026 | Leafly" (dispensary list)
- "Blue Dream Weed Strain Information | Leafly" (strain page)

All are keyword-rich, action-oriented, and include brand. The "Updated 2026" pattern on listing pages is a known SEO tactic (freshness signal). Our auto-generated titles like "Product | CannabisCompare" won't rank.

### Schema Markup
Leafly implements:
- `WebSite` with `SearchAction` on homepage (enables Google Sitelinks search)
- `Product` + `AggregateRating` on product/strain pages (enables rich snippets with star ratings in SERPs)
- `BreadcrumbList` throughout (helps crawlability and SERP display)
- `Store` schema on dispensary pages (enables Google Maps/local results)
- `FAQPage` on strain pages (enables FAQ rich snippets)

CannabisCompare has none of these. Adding `Product` + `AggregateRating` schema to product detail pages is a single Next.js component change and could unlock star ratings in Google results.

### Content Depth
Leafly's Cannabis 101 section has 11,000+ articles. This is years of SEO compounding. We don't need to match it — but **5-10 evergreen Utah-specific pages** (e.g., "Utah Medical Cannabis: What Patients Need to Know," "How to Get a Utah MMJ Card," "Utah Dispensary Locations Map") would capture high-intent local search traffic that Leafly doesn't specifically target.

### Internal Linking
Leafly links strains → related strains → dispensaries → products → articles in a web. Our site currently has limited cross-linking (product detail → dispensary is one of the few). Adding "Products at this dispensary" on dispensary pages, and "Find this product at other dispensaries" on product pages would improve both UX and crawl depth.

---

## Prioritized Recommendations for CannabisCompare

### 1. 🔴 Add strain-type, THC% range, and effects filters to product search
**Observed on**: leafly.com/shop
**What they do**: Filter sidebar includes Indica/Sativa/Hybrid tiles, THC% buckets (None/Low/Medium/High), and a list of effects (Relaxed, Sleepy, Euphoric, etc.) with counts.
**Recommended action**: Add three new filter dimensions to `/products/search`: strain_type (enum), thc_range (bucketed), and effects (multi-select tag list). All data is already stored or derivable. This is the single highest-impact discovery improvement for patients who search by "something to help me sleep."

### 2. 🔴 Surface the deals/promotions data already being scraped
**Observed on**: leafly.com/dispensaries/utah
**What they do**: Each dispensary card shows active deal count; deals are browsable at `/deals`.
**Recommended action**: Create a `/deals` route displaying current promotions per dispensary, and show deal count badge on dispensary cards. The scraper already collects `ScrapedPromotion` objects — this is purely a frontend display gap.

### 3. 🔴 Switch product and dispensary URLs to keyword-based slugs
**Observed on**: leafly.com URL structure
**What they do**: `/strains/blue-dream`, `/dispensaries/utah/salt-lake-city/the-flower-shop` — every URL is crawlable and keyword-rich.
**Recommended action**: Add `slug` fields to `Product` and `Dispensary` models (generate from name on creation). Update Next.js dynamic routes from `[id]` to `[slug]` with ID fallback for backwards compatibility. This unlocks all future SEO value.

### 4. 🔴 Add Product + AggregateRating JSON-LD schema to product detail pages
**Observed on**: leafly.com/strains/blue-dream
**What they do**: Schema markup enables star ratings to appear directly in Google search results (rich snippets).
**Recommended action**: Add a `<script type="application/ld+json">` block to `/products/[id]` that emits Product schema with `aggregateRating` pulled from existing review data. Single component, high SEO ROI.

### 5. 🔴 Show dispensary hours and open/closed status
**Observed on**: leafly.com/dispensaries/utah
**What they do**: Each dispensary card shows "Closed until 11am MT" or "Pickup in under 30 mins" — patients know before they drive.
**Recommended action**: Add a `hours` JSON field to the `Dispensary` model. Scrape it once during setup (it rarely changes). Compute and display open/closed status on both the dispensary list and detail pages.

### 6. 🔴 Add product images via a canonical cannabis product image database
**Observed on**: All Leafly product/strain pages
**What they do**: Every product card and detail page includes a product photo; strain pages have distinctive photography.
**Recommended action**: Integrate a cannabis product image API (e.g., Weedmaps has one; alternatively fetch from the dispensary's own product page which often has images). Even a fallback category illustration (flower = leaf icon, edible = gummy icon) dramatically improves card scanability over text-only.

### 7. 🟡 Add sort options to product search results
**Observed on**: leafly.com/shop
**What they do**: Sort by Recommended, Distance, Highest Rated, Most Reviews, A-Z.
**Recommended action**: Add sort controls to `/products/search` for at minimum: price (low→high, high→low), THC% (high→low), and relevance. The backend already has all needed columns.

### 8. 🟡 Display trust metrics prominently on the homepage
**Observed on**: leafly.com hero region
**What they do**: "11,000+ articles," "5,000+ strains," "1.3mm+ reviews" — displayed as social proof stats.
**Recommended action**: Add a stat strip to the homepage: "X products tracked · 10 Utah dispensaries · Prices updated every 2 hours." Pull live counts from the API. These are credibility signals for new patients.

### 9. 🟡 Write keyword-rich meta titles and descriptions for key pages
**Observed on**: Leafly title tags throughout
**What they do**: Every page has a hand-crafted, keyword-rich title tag. Dispensary list: "The Best Dispensaries Near Me in Utah | Updated 2026 | Leafly."
**Recommended action**: Add explicit `generateMetadata()` exports to the 5 highest-traffic Next.js routes (home, search, dispensary list, product detail, dispensary detail) with keywords, location signals, and freshness indicators.

### 10. 🟡 Create 5–10 Utah-specific SEO landing pages
**Observed on**: leafly.com/news/cannabis-101 (11,000 articles)
**What they do**: Leafly's content library drives massive organic traffic; we can't match scale but can own the Utah niche.
**Recommended action**: Create static pages targeting high-intent Utah queries: "Utah MMJ dispensaries," "how to get a Utah medical cannabis card," "cheapest cannabis in Utah," "Utah dispensary hours." These are low-effort, high-value pages that Leafly doesn't optimize for.

### 11. 🟡 Add terpene data to product detail pages
**Observed on**: leafly.com/strains/blue-dream
**What they do**: Myrcene, Pinene, Caryophyllene displayed with brief descriptions. Patients researching specific terpenes land here from Google.
**Recommended action**: Add optional `terpenes` JSON field to products (populated where scraper data or a third-party DB like CCDB provides it). Display as a simple tag list on the product detail page.

### 12. 🟢 Add a simple email capture ("Weekly Utah deals") below the fold
**Observed on**: leafly.com (twice below fold)
**What they do**: Newsletter sign-up with minimal friction.
**Recommended action**: Add a single newsletter sign-up row to the homepage and dispensary pages. "Get the week's best Utah dispensary deals emailed to you." Use the existing SendGrid integration for delivery.

### 13. 🟢 Add "Recently Viewed" products
**Observed on**: Leafly (various recommendation patterns)
**What they do**: Implicit personalization reduces friction on return visits.
**Recommended action**: Store last 10 viewed product IDs in localStorage; display a "Recently viewed" horizontal scroll on the homepage and search page. No backend changes needed.

---

## Raw Notes

- **JS-heavy pages**: The Leafly shop page renders a React SPA; filter counts and dispensary distances are dynamically loaded. The WebFetch extraction captured the initial HTML/SSR output which was sufficient for analysis.
- **Online ordering integration**: Leafly has deeply integrated with dispensary POS systems (Dutchie, Jane, etc.) to enable "Add to cart" and same-day delivery ordering. This is a multi-year platform investment and likely out of scope for CannabisCompare in the near term, but worth noting as the direction the market is heading.
- **Medical vs. recreational framing**: Leafly serves both markets; their compliance messaging is light. CannabisCompare is medical-only in Utah — this is a differentiator worth leaning into (more clinical trust signals, more patient-focused language).
- **"Updated 2026" title tag pattern**: Leafly's dispensary listing title includes "Updated 2026" as a freshness signal for Google. Simple to replicate in `generateMetadata()`.
- **Leafly Picks**: Curated editorial recommendations (e.g., "Best THC drinks 2026"). Low priority for us but an eventual monetization path via dispensary partnerships.
- **Social impact / equity section**: Leafly has a prominent social equity initiative page. Cannabis social equity is a real issue in Utah — could be a meaningful differentiator in brand positioning, not just compliance.
