# Repo audit and local/global boundaries

Concise audit of the G-Trade workspace and classification of what belongs in the repo vs global config. Used by the AI operating layer; do not treat as product architecture.

## Stack and structure

| Item | Finding |
|------|--------|
| **Workspace shape** | Composite: root not a git repo; git history in `es-hotzone-trader/` only. |
| **Stacks** | Python 3.11 (es-hotzone-trader, railway/ingest, analytics, mcp); Next.js (railway/web). |
| **Package managers** | pip/setuptools (pyproject.toml); npm (railway/web). |
| **Entry points** | CLI: `es-trade` → `src.cli.commands:main`; Railway: `app.py` per service; web: Next.js app. |
| **Test/lint/build** | pytest, ruff, black (pyproject); npm run dev/build/start (web). |
| **CI** | None (no .github/workflows). |
| **Docs** | docs/ (architecture, operator, compliance, runbooks, research, state, tasks). |
| **Cursor config** | .cursor/rules (one rule), .cursor/plans, .cursor/agents, .cursor/skills, .cursor/mcp.json. |
| **Issue/branch/PR** | No formal convention docs; Linear mentioned in Current_Plan for future work. |
| **Railway** | Documented in docs + rule + skill; deploy via Railway only. |
| **Docs generation** | None; no script producing dependency/module/routes maps. |

## Classification: local vs global vs hybrid

| Artifact | Where | Why |
|----------|--------|-----|
| AGENTS.md, .cursor/rules, docs tree, PR/issue templates, docs-generation script, .cursorignore | **COMMIT TO REPO** | Repo-specific behavior and conventions. |
| Hooks (destructive guard, branch/issue reminders, sensitive-file flags) | **GLOBAL USER/TEAM** | Apply across workspaces; install in user/team Cursor or shell config. |
| MCP server URLs, API keys, Linear/GitHub/Railway auth | **GLOBAL USER CONFIG** or **MANUAL EXTERNAL** | Never commit secrets; auth is per-user or team admin. |
| Reusable templates (AGENTS, rules pack, docs skeleton, playbooks) | **HYBRID** | Template lives in repo under docs/engineering-system/global-cursor-pack/; copy or init script for new repos. |
| Linear workspace, GitHub org/repo settings, Railway project | **MANUAL EXTERNAL ADMIN STEP** | Cannot be applied from inside repo. |
| OpenViking service and ingestion | **GLOBAL / EXTERNAL** | Durable knowledge layer; config and refresh are user/team or external. |

## Modules deserving docs/maps

- `es-hotzone-trader/src/`: cli, engine, execution, market, observability, bridge, server, strategies, indicators, config.
- `railway/`: ingest, analytics, mcp, web (each with app entry and env contract).
- Config surface: `es-hotzone-trader/config/default.yaml`, env vars (documented in OPERATOR.md).
