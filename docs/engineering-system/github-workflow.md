# GitHub workflow

Contract for branches, commits, PRs, and review. Supports both issue-driven and exploratory work. Conventions apply **per repo**; the G-Trade workspace and es-hotzone-trader use Linear project G-Trade (team GDG) and branch prefix GDG where applicable.

## Branch naming

- **With issue:** `fix/GDG-211-short-description`, `feat/GDG-212-feature-name`. Use team/issue prefix (GDG for this repo).
- **Exploratory:** `dev/short-description` or `topic/short-description`. No need to invent an issue ID.

## Commit messages

- Reference the issue when one exists (e.g. "Fix bridge retry GDG-211"). Keep first line concise; add detail in body if needed.
- Conventional commits (feat:, fix:, docs:) are optional but acceptable.

## PR naming and body

- Title: reflect the change (e.g. "Fix bridge retry when ingest returns 5xx" or "GDG-211 Fix bridge retry").
- Body: use the repo PR template. Link to Linear (or other) issue if applicable. Summarize what changed, what was tested, and any follow-up.

## Review and merge readiness

- Run tests and lint before marking ready. Ensure docs are updated if behavior or config changed.
- Human review for non-trivial or safety-relevant changes. Automated agents should not merge without explicit user approval unless the team has configured otherwise.

## Minimal MCP/permissions

- Prefer minimal GitHub MCP scope (e.g. read + PR create/update, no direct merge or branch delete) unless the user has configured more. Document what the agent may do vs what requires human review.
