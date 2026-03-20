# Local vs global

Classification of what belongs in the repo (commit) vs user/team config (outside repo).

## Commit to repo

- AGENTS.md, .cursor/rules/*, docs tree, PR/issue templates, scripts/generate_docs_index.py, .cursorignore, .cursorindexingignore.
- Repo-specific conventions and workflow docs. Reusable templates are archived under `docs/archive/engineering-system-global-cursor-pack/`; installation remains a global/manual step.

## Global user config

- Cursor settings (e.g. MCP server list, optional hooks). MCP credentials and API keys (never in repo).
- Linear/GitHub auth tokens and any external service credentials. OpenViking service URL and auth if used.

## Global team config

- Shared Linear workspace, GitHub org/repo settings, branch protection, and review policies. These are manual admin steps.

## Hybrid (template in repo + manual global install)

- Hooks: templates in repo under `docs/archive/engineering-system-global-cursor-pack/hooks/`; installer or copy to user/team Cursor or shell config.
- MCP: example configs in repo (no secrets); real URLs and tokens in user .cursor/mcp.json or Cursor settings.
- Reusable rule pack and AGENTS template: copy or run an init script for new repos.

## Manual external admin step

- Creating or linking Linear workspace or GitHub repo. Enabling MCP servers in Cursor UI. Anything requiring authentication or admin UI.

See [repo-audit-and-boundaries.md](repo-audit-and-boundaries.md) for the audit and classification table.
