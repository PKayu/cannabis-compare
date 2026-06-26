# Scraper QA Report — 2026-04-07

## Run Summary
| Scraper | Status | Products Found | Processed | Flags | Duration |
|---------|--------|---------------|-----------|-------|----------|
| wholesomeco | success | 736 | - | 1 | 102s |
| curaleaf-lehi | running* | (prev: 294) | - | (prev: 5) | (prev: 505s) |
| curaleaf-provo | success | 413 | - | 0 | 516s |
| curaleaf-springville | running* | (prev: error) | - | - | (prev: 502s) |
| curaleaf-park-city | success | 536 | - | 0 | 97s |
| beehive-brigham-city | success | 200 | - | 1 | 41s |
| beehive-slc | success | 133 | - | 1 | 39s |
| zion-medicinal | success | 293 | - | 0 | 135s |
| dragonfly-slc | success | 93 | - | 0 | 38s |
| dragonfly-price | success | 1133 | - | 0 | 26s |
| bloc-south-jordan | success | 177 | - | 3 | 41s |
| bloc-st-george | success | 194 | - | 2 | 40s |
| flower-shop-logan | success | 261 | - | 5 | 55s |
| flower-shop-ogden | success | 240 | - | 3 | 63s |
| the-forest-murray | success | 273 | - | 2 | 60s |

\* Still running at time of report (>15 min); previous run data shown.

**Total products scraped (completed runs)**: ~4,679

## Quality Scores
| Check | Result | Status |
|-------|--------|--------|
| Run Health | 13/15 completed; curaleaf-springville errored (prev run), curaleaf-lehi/springville stuck running | &#x26A0;&#xFE0F; |
| Flag Rate | 0.5% overall (24 flags / ~4,679 products) | &#x2705; |
| URL Coverage | 100% (22,755/22,755 prices have product_url) | &#x2705; |
| Price Sanity | 0 extreme outliers (<$5 or >$500) | &#x2705; |
| Field Coverage | 80.5% missing THC, 87.5% flags have weight+URL | &#x26A0;&#xFE0F; |
| Pending Backlog | 24 pending flags (all pending_cleanup) | &#x26A0;&#xFE0F; |

## Critical Issues

### 1. Curaleaf Scrapers: SQLite "database is locked" Crashes (CRITICAL)
**Root cause identified**: Curaleaf Lehi, Provo, and Springville scrapers fail with `PendingRollbackError` caused by `sqlite3.OperationalError: database is locked`. Success rates over 7 days: Provo 15.8%, Springville 37.5%, Lehi 50%.

The crash occurs when `scraper_runner.py` tries to UPDATE `scraper_runs.dispensary_id` — the flush hits a SQLite write lock from another concurrent scraper subprocess, the session auto-rolls-back, and all subsequent DB operations fail with `PendingRollbackError`.

**Contributing factor**: All three scrapers shared `dispensary_name="Curaleaf"`, causing them to contend on the same dispensary row.

### 2. "hardware" Category Dominance (WARNING)
14,553 of 18,952 master products (76.8%) are categorized as "hardware". This is almost certainly a default-category bug — real hardware products should be a small fraction.

### 3. THC/CBD Data Gap (WARNING)
80.5% of master products missing THC data, 92.6% missing CBD. This degrades confidence scorer matching quality.

## Fixes Applied

### Curaleaf Scraper — Fix 1: Unique dispensary names per location
**Issue**: curaleaf-lehi, curaleaf-provo, and curaleaf-springville all used `dispensary_name="Curaleaf"`, causing all three to write to the same dispensary record. This violates the multi-location rule documented in CLAUDE.md and creates unnecessary DB row contention.
**File**: `backend/services/scrapers/curaleaf_scraper.py`
**Change**: Updated `dispensary_name` to `"Curaleaf Lehi"`, `"Curaleaf Provo"`, and `"Curaleaf Springville"` respectively. Each location now gets its own dispensary record, matching the pattern already used by Park City (`"Curaleaf Park City"`).

### Database — Fix 2: SQLite WAL mode + busy timeout
**Issue**: SQLite database had no WAL mode or busy timeout configured. Concurrent scraper subprocesses caused immediate "database is locked" errors instead of waiting for the lock to clear.
**File**: `backend/database.py`
**Change**: Added SQLite-specific configuration:
- `PRAGMA journal_mode=WAL` — allows concurrent reads during writes
- `PRAGMA busy_timeout=30000` — waits up to 30s for write lock instead of failing immediately
- `connect_args={"timeout": 30}` — Python sqlite3 driver-level timeout
These are applied via SQLAlchemy `event.listens_for(engine, "connect")` so every connection (including subprocess connections) gets the pragmas.

### Scraper Runner — Fix 3: Retry logic for dispensary update
**Issue**: When the dispensary_id UPDATE hits a SQLite lock, the session enters `PendingRollbackError` state and the entire scraper run fails. No recovery was attempted.
**File**: `backend/services/scraper_runner.py`
**Change**: Wrapped the dispensary lookup + `run_log.dispensary_id` update in a retry loop (3 attempts) that catches `database is locked` / `PendingRollbackError`, issues `session.rollback()`, re-fetches the detached run_log, and retries after a short backoff.

## Deferred Improvements (not auto-applied)

1. **"hardware" category audit** — Requires querying products where `category='hardware'` and inspecting names to determine if the bug is in scraper extraction or confidence scorer default assignment. Too broad for an automated fix.

2. **THC/CBD data enrichment** — 80.5% of master products lack THC data. The Curaleaf scraper already extracts THC from `fullText` when available, but most products don't display it on category pages. Would require navigating to individual product detail pages, which would increase scrape time significantly.

3. **Dismiss junk flag** — Flag `223e0ede-0e60-40cb-8a54-319a519216c3` is "your first app order" from wholesomeco (score 0.42), a promotional banner scraped as a product. Should be dismissed and a filter added to the wholesomeco scraper.

4. **curaleaf-payson zombie detection** — Disabled scraper had avg duration of 64,652s (~18h) before being disabled. The `scraper_subprocess.py` 600s timeout should have caught this; investigate if the timeout isn't being enforced for all code paths.
