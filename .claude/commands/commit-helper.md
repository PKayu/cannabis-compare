# Commit Helper

## Steps

1. **Run the Commit Helper**
   - Execute `py scripts/commit_helper.py`
   - Or use the batch file: `scripts\commit-helper.bat`

2. **Review Uncommitted Changes**
   - Changes are grouped by category (backend, frontend, scrapers, tests, docs)
   - Line changes shown (+add/-remove) for each file

3. **Choose What to Commit**
   - Enter a number (1-9) to commit a specific group
   - Enter `s` to select specific files
   - Enter `a` to commit all changes (grouped logically)
   - Enter `q` to quit without committing

4. **Review Commit Message**
   - AI suggests a conventional commit message based on file types
   - Edit or accept the suggestion
   - Optionally add Co-Authored-By header

5. **Changes are Committed**
   - Files are automatically staged
   - Commit is created with your message
   - Git hooks validate syntax and format

## Example Output

```
======================================================================
UNCOMMITTED CHANGES
======================================================================

[SCRAPER] (1 file)
  [untracked ] backend/services/scrapers/curaleaf_scraper.py

[FRONTEND-COMPONENTS] (1 file)
  [modified  ] frontend/components/PriceComparisonTable.tsx
              +11/-9

[API] (2 files)
  [modified  ] backend/routers/products.py
              +5/-2
```

## Notes

- Use this after working with AI on multiple changes
- Keeps commits organized by logical grouping
- Works alongside git hooks (pre-commit validation still runs)
- Can be run multiple times to commit different groups separately
