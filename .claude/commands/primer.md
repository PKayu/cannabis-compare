# Primer Command

## Steps

1. **Understand Project Structure**
   - Run `tree` or equivalent to visualize the directory structure
   - Focus on top-level organization (backend/, frontend/, docs/, etc.)

2. **Read Core Documentation**
   - Start with CLAUDE.md (project guidelines and patterns)
   - Read README.md (if exists) for project overview
   - Skim ARCHITECTURE.md for system design decisions

3. **Identify Key Files**
   - backend/models.py (database schema)
   - backend/main.py (API setup)
   - frontend/lib/api.ts (frontend API client)
   - frontend/app/layout.tsx (frontend structure)

4. **Search and Explore**
   - Use Grep or Task/Explore agent to search codebase
   - If search fails, retry with alternative search approaches
   - Focus on understanding current implementation status
   - Look for TODOs, incomplete sections, or active workflows

5. **Provide Summary**
   - Output a concise project status report
   - Highlight current state, recent changes, and next steps
   - Note any active development work or blockers

IMPORTANT: Use Serena to serach through the codebase. IF you get any errors using Serena, retry with different Serena tools.

## Notes

- All searches should be case-insensitive where appropriate
- Prioritize reading existing documentation over raw code exploration