# Codex Workflow Guide

This guide defines the Codex-first workflow for `cannabis compare` while keeping existing Claude assets in place.

## Scope

- Codex behavior contract: `AGENTS.md`
- Claude behavior contract: `CLAUDE.md`
- Codex reference docs: `docs/codex/*`

## Task Folder Contract (Strict)

For non-trivial work, use:

`dev/active/<task-slug>/`

Required files:

- `<task-slug>-plan.md`
- `<task-slug>-context.md`
- `<task-slug>-tasks.md`

Each file must include:

- `Created`
- `Last Updated`
- `Status`

## Standard Execution Flow

1. Run primer workflow before implementation.
2. Create or load the task triad.
3. Populate explicit checklist items in `*-tasks.md`.
4. Implement in small verifiable increments.
5. Update context and task checkboxes continuously.
6. Run focused validation.
7. Group and commit changes logically.
8. Synchronize affected documentation.

## Codex Skill Set (Global User Scope)

Installed globally under user Codex skills:

- `project-primer`
- `task-folder-manager`
- `commit-orchestrator`
- `doc-sync-manager`
- `instruction-maintainer`

### Suggested Invocation Patterns

- "Use `project-primer` for this feature."
- "Use `task-folder-manager` and set up a new active task."
- "Use `commit-orchestrator` to prepare grouped commits."
- "Use `doc-sync-manager` to reconcile docs."
- "Use `instruction-maintainer` to update AGENTS learnings."

## Cross-Reference to Existing Claude Assets

- Primer analog: `.claude/commands/primer.md`
- Commit analog: `.claude/commands/commit-helper.md` and `scripts/commit_helper.py`
- Instruction maintenance analog: `.claude/commands/revise-claude-md.md`
- Documentation sync analog: `.claude/agents/documentation-manager.md`
- Context specialist analog: `.claude/agents/code-context-specialist.md`

## Trivial vs Non-Trivial Guidance

Use direct implementation only when clearly trivial:

- one small isolated edit
- no workflow/process implications
- no significant cross-file impact

Everything else should use the task triad workflow.

## Validation Scenarios

1. Large task prompt:
   "Implement feature X across backend + frontend."
   Expected: task triad established/read before major implementation.
2. Resume prompt:
   "Continue work on <task>."
   Expected: read existing plan/context/tasks first.
3. Commit prompt:
   "Commit all changes."
   Expected: grouped logical commits with conventional prefixes.
4. Wrap-up prompt:
   "Wrap up."
   Expected: documentation sync check occurs.
5. Coexistence prompt:
   Prompt references Claude files.
   Expected: Codex-native execution while preserving `.claude/*`.
