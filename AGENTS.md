# Agent guide — G-Trade

This file is the repository operating contract for AI agents working in `G-Trade`.

## Repo purpose

`G-Trade` is the canonical repo for:

- `src/`, `config/`, `tests/`, and `pyproject.toml` — the active local trading system
- `docs/` — operator, architecture, research, and archive notes
- `scripts/` — repo and trader utilities
- `.cursor/` and `.codex/` — project-specific AI operating assets

The active stack is local-only:

- Python
- CLI
- local Flask console
- SQLite
- Topstep

Railway and MCP are retired from the active workflow. Historical references live under [`docs/archive/railway-sunset/README.md`](docs/archive/railway-sunset/README.md).

## Core architecture rules

1. Execution and Topstep stay on the Mac.
2. SQLite is the source of truth for runs, events, snapshots, market tape, order lifecycle, and trade review.
3. The CLI and local Flask console are the operator surfaces.
4. No cloud dependency is required to trade, debug, or review the system.
5. Do not reintroduce a cloud-to-executor control path.

## Project layout

- `src/`
  - `cli/` — operator commands
  - `analysis/` — regime packet and trade review analysis
  - `engine/` — strategy, regime logic, exits, scheduling
  - `execution/` — order execution and reconciliation
  - `market/` — Topstep client and broker truth
  - `observability/` — SQLite durability
  - `server/` — local Flask console, SSE, `/health`, `/debug`
- `config/` — runtime defaults
- `tests/` — trader test suite
- `docs/` — active docs
- `docs/archive/` — historical materials
- `scripts/` — repo and trader utilities

## Start here

Before structural or behavioral changes, read:

- [`docs/README.md`](docs/README.md)
- [`docs/architecture/overview.md`](docs/architecture/overview.md)
- [`docs/OPERATOR.md`](docs/OPERATOR.md)
- [`docs/Current-State.md`](docs/Current-State.md)
- [`docs/Compliance-Boundaries.md`](docs/Compliance-Boundaries.md)

## Documentation contract

Update docs when you change:

- CLI surface
- Flask console behavior
- config keys
- launchd/runtime workflow
- strategy or exit behavior
- compliance-relevant behavior
- repository structure

Generated docs under `docs/generated/` are machine-maintained. Do not hand-edit them.

## Testing contract

- Run relevant tests before completing a change.
- For trader/runtime changes, prefer `pytest` from the repo root.
- Do not remove or disable tests without a documented reason.

Useful commands:

- `pytest`
- `ruff check .`
- `black .`

## Git contract

- `G-Trade` is the only active repo.
- Do not recreate nested Git repositories inside the workspace.
- Prefer issue-linked branches when a Linear issue exists.
- Keep commits coherent and scoped.

## Safety constraints

- Do not add execution or broker logic outside `src/`.
- Do not add secrets or live credentials to the repo.
- Treat `.env`, `.cursor/mcp.json`, and `.codex/config.toml` as local-only files.
- Use example files for committed config scaffolding.
- Avoid destructive commands like `git reset --hard` or `git checkout --` unless explicitly requested.

## Available project skills

- `agents-orchestrator`
- `es-hotzone-debug`
- `issue-to-pr`
- `use-openviking`
- `upstash` (only if explicitly needed later)

## Subagent routing

Use at most two subagents at a time.

| Task type | Subagent |
|-----------|----------|
| Broad codebase search | `explorer` |
| Code review | `code-reviewer` |
| API/runtime validation | `api-tester` |
| UI/runtime evidence | `evidence-collector` |
| Performance analysis | `performance-benchmarker` |
| Docs | `technical-writer` |
| Security review | `security-engineer` |
| Status / synthesis | `openviking-analyst` |

## What requires extra care

- `src/engine/`
- `src/execution/`
- `src/market/`
- `src/observability/`
- launchd workflow and local runtime ports
- compliance docs and runbooks

## Historical references

- Nested repo import record: [`docs/archive/repository-imports-2026-03-19.md`](docs/archive/repository-imports-2026-03-19.md)
- Railway retirement notes: [`docs/archive/railway-sunset/README.md`](docs/archive/railway-sunset/README.md)
