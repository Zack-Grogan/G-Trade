# Linear workflow

Contract for how work flows with Linear (when used). Linear is the work/planning source of truth; Cursor and GitHub follow it.

For this repo, the Linear project is **G-Trade** (team GDG); use issue IDs like GDG-211 in branches and commits.

## Issue lifecycle during development

- **Backlog / Triage:** Issues could be unprioritized or not yet development-ready. Triage produces development-ready work (clear scope, acceptance criteria if applicable).
- **In progress:** When starting work, move issue to In Progress (or team equivalent). Branch and commits should reference the issue ID where possible.
- **Exploratory work:** If there is no issue yet, work is development-stage. When formalizing, create or backfill an issue and link branch/PR to it.

## When an issue exists

- Create a branch that references the issue (e.g. `fix/PROJ-123-short-name`, `feat/PROJ-456-feature-name`). Use team prefix if defined.
- Reference the issue in commit messages (e.g. "Fix login redirect PROJ-123") and in the PR title/body.
- When the PR is merged or work is done, transition the issue (e.g. Done) per team process.

## When work is exploratory

- No need to create an issue upfront. Document discoveries; propose creating an issue (or plan item) when you want to track the work formally.
- When backfilling: create the issue, then add the issue ID to the branch name or PR for traceability if the branch already exists.

## Fields and labels

- Use status/state to reflect reality (e.g. In Progress when actively coding). Labels can denote type (bug, feature, docs) or area; use what the team already has rather than inventing new schemes.

## Agent guidance

- At workspace level: prefer issue-aware branch/commit/PR when an issue is present; allow exploratory work without blocking on issue creation.
- Do not assume Linear is configured or that the user has an API key; follow the conventions in docs and use MCP only when the user has set it up.
