# Codex Operating Contract - cannabis compare

This file defines how Codex should operate in this repository. It is the authoritative instruction source for Codex behavior in this repo.

`CLAUDE.md` remains the authoritative instruction source for Claude-specific workflows. Keep both systems side-by-side.

## Core Mode

- Use a strict task-folder gate for non-trivial work.
- Prefer deterministic, incremental execution over one-shot broad edits.
- Keep documentation synchronized with code changes.
- Keep commits logically grouped using conventional commit types.

## Strict Task-Folder Gate

For non-trivial requests (cross-file, multi-step, or anything likely to exceed a single focused edit), Codex must use:

`dev/active/<task-slug>/`

Required files:

- `<task-slug>-plan.md`
- `<task-slug>-context.md`
- `<task-slug>-tasks.md`

Required headers in each file:

- `Created`
- `Last Updated`
- `Status`

### Gate Rules

1. Before substantial implementation, check if a matching active task folder already exists.
2. If it exists, read plan/context/tasks fully before editing code.
3. If it does not exist, create the folder and the three required files first.
4. Keep the checklist in `*-tasks.md` current as work progresses.
5. Update `Last Updated` and status markers as soon as state changes.

### Allowed Bypass

Direct implementation without task folder is allowed only for clearly trivial work:

- single-file typo/text fix
- one-command informational request
- very small isolated change with no workflow impact

When in doubt, create/use the task folder.

## Primer-First Workflow

Before implementation on non-trivial work:

1. Read `CLAUDE.md` and `README.md`.
2. Inspect relevant architecture/docs (`docs/ARCHITECTURE.md`, `docs/INDEX.md`, targeted guides).
3. Locate implementation entry points with fast search.
4. Summarize current-state understanding in task context notes.

Mirror of Claude reference: `.claude/commands/primer.md`.

## Implementation Lifecycle

1. Define or load task scope from the task triad.
2. Convert scope into explicit checklist items in `*-tasks.md`.
3. Implement in small verifiable steps.
4. Record key decisions, touched files, and follow-ups in `*-context.md`.
5. Mark completed checklist items immediately.
6. Run focused validation relevant to the change.

## Commit Protocol

Group changes by logical area before commit:

- backend
- frontend
- scrapers
- tests
- docs
- config/chore

Use conventional commit prefixes:

- `feat`
- `fix`
- `refactor`
- `test`
- `docs`
- `chore`

Reference implementation tooling:

- `scripts/commit_helper.py`
- `.claude/commands/commit-helper.md`

## Documentation Synchronization

After meaningful code changes, review and update affected docs:

- `README.md` for setup/workflow changes
- `docs/ARCHITECTURE.md` for architectural changes
- `docs/API_TEST_PLAN.md` for test/endpoint changes
- relevant `docs/guides/*` for operational changes
- task triad records under `dev/active/<task>/`

Mirror of Claude reference:

- `.claude/agents/documentation-manager.md`
- `.claude/commands/revise-claude-md.md`

## Review Expectations

When asked to review, prioritize:

1. functional bugs and regressions
2. risk and edge-case failures
3. missing validation/tests for changed behavior
4. contract mismatches between frontend/backend/docs

Avoid spending primary review effort on minor style-only nits.

## Coexistence Rules (Claude + Codex)

- Do not remove or rewrite `.claude/*` as part of Codex workflow setup.
- Prefer adding Codex-native docs in `docs/codex/` and cross-linking.
- Keep shared process semantics aligned across both systems.
- If a rule conflicts, follow the active agent system for the current session.

## Skill Contract (Global User Skills)

This repository expects the following Codex skills to exist in user scope:

- `project-primer`
- `task-folder-manager`
- `commit-orchestrator`
- `doc-sync-manager`
- `instruction-maintainer`

See `docs/codex/WORKFLOW.md` for usage and trigger guidance.
