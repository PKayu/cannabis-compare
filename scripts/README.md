# Documentation Cleanup Script

A comprehensive bash script that automatically audits and reports on documentation health, organization, and consistency.

## Usage

```bash
bash scripts/cleanup-docs.sh
```

Or make it executable first:

```bash
chmod +x scripts/cleanup-docs.sh
./scripts/cleanup-docs.sh
```

## What It Checks

### 1. Naming Conventions
- Root level docs should follow `UPPERCASE_SNAKE_CASE.md` or `lowercase.md` pattern
- Workflow files should follow `NN_description_STATUS.md` pattern (e.g., `08_user_authentication_COMPLETED.md`)
- Flags files that don't match expected conventions

### 2. File Organization
- Verifies critical directories exist: `docs/`, `docs/workflows/`, `docs/archive/`
- Reports structural issues

### 3. Redundancy Check
- Detects TODO/FIXME/XXX markers indicating incomplete documentation
- Finds placeholder text like `[PLACEHOLDER]` or `[TBD]`
- Reports counts of incomplete sections

### 4. Workflow Progress
- Analyzes status of all workflows (COMPLETED, IN_PROGRESS, PENDING)
- Calculates overall completion percentage
- Shows detailed breakdown

### 5. Documentation Health
- Counts total documentation files
- Reports breakdown by location (root, workflows, archived)
- Provides quick overview of documentation volume

### 6. Critical Files Check
- Verifies existence of essential documentation:
  - `docs/ARCHITECTURE.md`
  - `docs/GETTING_STARTED.md`
  - `docs/prd.md`
  - `docs/workflows/README.md`
  - `CLAUDE.md`

### 7. Summary Report
- Consolidated view of all findings
- Exit code indicates status:
  - `0` = No issues found
  - `1` = Issues detected (exit code only, script continues)
- Actionable recommendations

## Output

The script uses colored output for clarity:

- 🔵 **Blue** (`▶`) = Section headers
- 🟢 **Green** (`✓`) = Passed checks
- 🟡 **Yellow** (`⚠`) = Warnings (review recommended)
- 🔴 **Red** (`✗`) = Issues requiring action

## Example Output

```
╔════════════════════════════════════════╗
║   Documentation Cleanup Script 📚      ║
╚════════════════════════════════════════╝

▶ 1. Checking Naming Conventions
⚠ Workflow naming: 08_user_authentication.md (expected NN_description_STATUS.md)

▶ 2. Checking File Organization
✓ File organization is correct

▶ 3. Checking for Redundancy
⚠ Found 13 TODO/FIXME markers in documentation

▶ 4. Analyzing Workflow Progress
  Completed: 8/10
  In Progress: 1/10
  Pending: 1/10
  Overall Progress: 90%
✓ Workflow progress analyzed

▶ 5. Documentation Health Report
  Total Documentation Files: 36
  Root Level: 9
  Workflows: 11
  Archived: 13
✓ Documentation health report generated

▶ 6. Checking for Critical Files
✓ Found: docs/ARCHITECTURE.md
✓ Found: docs/GETTING_STARTED.md
✓ Found: docs/prd.md
✓ Found: docs/workflows/README.md
✓ Found: CLAUDE.md

▶ 7. Summary

⚠ 4 warnings found (review recommended)

Recommendations:
  1. Review warnings above and address naming/organization issues
  2. Archive outdated documentation to docs/archive/
  3. Review very old files and update if needed
  4. Resolve any TODO/FIXME markers

To commit changes:
  git add docs/
  git commit -m 'docs: cleanup and reorganization'
```

## Common Actions Based on Output

### If workflows have wrong naming:
Rename files to match pattern `NN_description_STATUS.md`:

```bash
# Example:
mv docs/workflows/08_user_authentication.md docs/workflows/08_user_authentication_IN_PROGRESS.md
```

### If TODO/FIXME markers found:
Review and resolve incomplete sections:

```bash
grep -r "TODO\|FIXME" docs --include="*.md"
```

### If critical files are missing:
Create them or check paths in CLAUDE.md for documentation structure.

## Scheduling

You can run this script:
- **Manually** before committing documentation changes
- **In CI/CD** as part of pre-commit hooks to enforce consistency
- **Periodically** (e.g., weekly) to maintain documentation health

## Future Enhancements

Possible additions to this script:

- Check for broken internal links and references
- Validate markdown syntax
- Measure documentation age and flag very old files
- Generate HTML report
- Integration with GitHub workflow checks
- Auto-fix common issues (renaming files, updating links)

## Troubleshooting

### Script hangs or runs slowly
The script uses file globbing and grep across many files. On very large projects, this may take several seconds. This is normal.

### Exit code 1 but warnings only
Exit code 1 indicates warnings or issues found, but the script completes successfully. Review the output and recommendations.

### Not executable
Make the script executable:

```bash
chmod +x scripts/cleanup-docs.sh
```

## Related Documentation

- See `CLAUDE.md` in the project root for overall documentation guidelines
- See `docs/` for all project documentation
- See `docs/workflows/` for implementation workflows
