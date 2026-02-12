# Context: Cleanup Queue Enhancement

## Key Files Modified
- `backend/models.py` - Added `issue_tags` column to ScraperFlag
- `backend/alembic/versions/20260208_180000_add_issue_tags_to_scraperflag.py` - New migration
- `backend/routers/admin_flags.py` - Added issue_tags to schemas and endpoint handlers
- `backend/services/normalization/flag_processor.py` - Accept & persist issue_tags; return in pending response
- `frontend/app/(admin)/admin/cleanup/hooks/useCleanupSession.ts` - Expanded interfaces
- `frontend/lib/api.ts` - Added issue_tags to approve/reject/dismiss types
- `frontend/app/(admin)/admin/cleanup/components/FlagCard.tsx` - Full rewrite with editing, comparison, tags, URL
- `frontend/app/(admin)/admin/cleanup/page.tsx` - Pass issueTags through handlers
- `frontend/app/(admin)/admin/cleanup/components/CleanupSwipeView.tsx` - Pass issueTags through handlers

## Key Decisions
- Click-to-edit pattern (not inline form) for field editing - less intrusive UX
- Weight regex patterns ported from Python weight_parser.py to JS for client-side smart actions
- Issue tags auto-detect but do NOT auto-apply - user must click to activate
- Tags support undo via snapshot mechanism
- Backend already returned matched_product, dispensary_name, etc. - frontend just wasn't using them
- dismiss API changed from `(flagId, notes)` to `(flagId, data)` to support issue_tags

## Last Updated
2026-02-08
