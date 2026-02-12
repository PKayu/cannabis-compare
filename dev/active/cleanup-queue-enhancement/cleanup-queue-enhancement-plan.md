# Enhanced Cleanup Queue: Inline Editing, Source URLs, and Issue Tags

## Context

The cleanup queue FlagCard showed read-only product data with just approve/reject/dismiss buttons. The backend already supported field edits on approve/reject, but the frontend never built the UI for it. Additionally, source URLs only showed when non-null, matched products showed only raw IDs, and there was no way to tag common data quality issues.

## Changes Made

### Phase 1: Backend - issue_tags Column
- New Alembic migration adding `issue_tags` (JSON, nullable) to `scraper_flags`
- Updated ScraperFlag model with `issue_tags` column
- Added `issue_tags` to Pydantic request schemas (approve, reject, dismiss)
- Updated endpoint handlers to forward issue_tags to processor
- Updated flag_processor to persist issue_tags and return them in pending response

### Phase 2: Frontend - Expanded Interfaces
- Added MatchedProduct interface with full product fields
- Expanded ScraperFlag interface with dispensary_name, matched_product, confidence_percent, merge_reason, issue_tags
- Updated api.ts flags wrapper with issue_tags support

### Phase 3+4: FlagCard Rewrite with Inline Editing & Issue Tags
- Click-to-edit fields with "Edit All" toggle
- Always-visible source URL (link or "No source URL available" placeholder)
- Matched product comparison with color-coded diffs (green = match, yellow = differs)
- 4 issue tags with smart actions: Weight in Name, Garbage in Name, Missing Fields, Wrong Category
- Tag undo support via snapshots

### Phase 5: Parent Component Updates
- page.tsx handlers updated to accept and forward issueTags
- CleanupSwipeView.tsx handlers updated to accept and forward issueTags

## Last Updated
2026-02-08
