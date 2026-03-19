---
name: issue-to-pr
description: Follows the issue-to-PR flow: read issue and docs, branch with issue ID, implement, test, docs, commit, PR with template. Use when the user is working from a Linear or other issue or asks to implement a ticket.
---

# Issue-to-PR workflow

Apply when the user has an issue (e.g. Linear) or asks to implement a ticket.

## Steps

1. **Read issue and context** — Description, acceptance criteria, labels. Read AGENTS.md and relevant architecture/module docs.
2. **Create branch** — Include issue ID when one exists: `fix/GTRADE-123-short-name` or `feat/GTRADE-456-feature-name`. Exploratory: `dev/short-description` or `topic/short-description`.
3. **Implement** — Implement narrowly; run relevant tests; update docs if behavior or config changed.
4. **Commit** — Reference issue in message (e.g. "Fix bridge retry GTRADE-123"). Conventional commits (feat:, fix:, docs:) optional.
5. **Open PR** — Use repo PR template. Link issue if applicable. Summarize changes, testing, and follow-up. Run tests and lint before marking ready.
6. **Issue status** — Mark In Progress when starting; move to Done when merged (if Linear MCP available and team process uses it).

## Conventions (one-line)

- **Branch:** `fix/GTRADE-123-short-name` or `feat/GTRADE-456-name` when issue exists.
- **Commit:** Issue ref in message; first line concise.
- **PR:** Template; link issue; summarize changes and testing.

## Subagent dispatch

Per rule 03-orchestration-first, dispatch to specialists when the task fits:

| Step | Subagent | When to use |
|------|----------|-------------|
| After implementation | **code-reviewer** | Review changes for correctness, security, maintainability before PR. |
| Test verification | **api-tester** | API or endpoint testing; validation and QA. |
| Test verification | **evidence-collector** | QA requiring visual evidence; screenshot-based verification. |
| Complex git operations | **git-workflow-master** | Rebases, conflict resolution, branch management, git history cleanup. |
| Running tests | **shell** | Execute pytest, lint, or other test commands. |

Max 2 subagents at a time. For complex workflows, run sequentially (e.g. shell for tests → code-reviewer for review).

## Full procedure

- Playbook: `docs/engineering-system/global-cursor-pack/operating-playbooks/starting-work-from-linear-issue.md`.
- Branch/commit/PR: `docs/engineering-system/github-workflow.md`, `docs/engineering-system/linear-workflow.md`.

Use the playbook for variants (exploratory, backfill issue, review/merge policy).
