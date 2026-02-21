# Cleanup Dashboard Improvements — Task Checklist

Last Updated: 2026-02-16

## Backend
- [ ] Phase 1: `name_cleaner.py` utility + wire into scorer + scraper_runner
- [ ] Phase 2: `thc_content`/`cbd_content` fields on Product + ScraperFlag models; Alembic migration
- [ ] Phase 3: Fuzzy matching weights (NAME 75%, BRAND 25%, THC 0%)
- [ ] Phase 4: Auto-merge → create ScraperFlag(status="auto_merged"); include_auto_merged filter param
- [ ] Phase 5: `merge_duplicate_flag()` in flag_processor; `POST /api/admin/flags/merge-duplicate/{flag_id}` endpoint
- [ ] Phase 6: `approve_flag()` accepts `matched_product_name`/`matched_product_brand` overrides

## Frontend
- [ ] Phase 7: FlagCard.tsx — fix Approve button disabled condition (line 480)
- [ ] Phase 8: FlagCard.tsx — edit-both-products section in approve flow
- [ ] Phase 9: Tab redesign — Priority Queue / Needs Cleanup / Duplicates / Auto-Linked / All Flags
- [ ] Phase 10: THC/CBD display uses `thc_content` text field

## Done
(move items here as completed)
