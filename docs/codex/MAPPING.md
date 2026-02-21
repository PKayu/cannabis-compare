# Claude to Codex Workflow Mapping

This document maps existing Claude workflow components to Codex equivalents.

## High-Level Mapping

| Claude Asset | Codex Equivalent | Notes |
|---|---|---|
| `CLAUDE.md` | `AGENTS.md` | Codex authoritative repo behavior contract |
| `.claude/commands/primer.md` | `docs/codex/WORKFLOW.md` + `project-primer` skill | Primer-first operating model |
| `.claude/commands/commit-helper.md` | `commit-orchestrator` skill | Uses same logical grouping and conventional commits |
| `scripts/commit_helper.py` | referenced by Codex commit protocol | Existing script remains source tooling |
| `.claude/commands/revise-claude-md.md` | `instruction-maintainer` skill | Session learnings flow for Codex instructions |
| `.claude/agents/code-context-specialist.md` | `project-primer` skill responsibility | Search-first context collection |
| `.claude/agents/documentation-manager.md` | `doc-sync-manager` skill | Documentation synchronization workflow |
| `.claude/skills/*` | global Codex skills | Codex skills are user-scoped per chosen preference |

## Task Structure Mapping

| Existing Pattern | Codex Contract |
|---|---|
| `dev/active/<task>/` | unchanged |
| `<task>-plan.md` | required |
| `<task>-context.md` | required |
| `<task>-tasks.md` | required |
| `Created`, `Last Updated`, `Status` headers | required |

## Behavioral Parity Notes

- Keep `.claude/*` unchanged.
- Add Codex-native process docs under `docs/codex/`.
- Preserve strict gating for non-trivial work.
- Preserve commit grouping and docs-sync discipline.
- Keep workflow semantics aligned between agent systems.
