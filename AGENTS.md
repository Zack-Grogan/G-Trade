# Agent guide — G-Trade / es-hotzone-trader

This file is the **repository operating contract** for AI agents. Read it before structural or behavioral changes. It orients agents to architecture, layout, conventions, and guardrails.

## Repo purpose

G-Trade is a workspace containing:

- **es-hotzone-trader:** CLI-based ES hot-zone day trading system. Execution and Topstep API run on the host (Mac); no TUI.
- **railway/:** Cloud services for the G-Trade Railway project (ingest, analytics, MCP, web). Analytics and tooling only; no execution or broker.

Human-maintained docs are the source of truth. Generated docs (e.g. from `scripts/generate_docs_index.py`) are machine-maintained indexes; do not treat them as overriding architecture or operator docs.

## Project layout

- **`es-hotzone-trader/`** — Local trading system (Python). CLI-only operator surface; execution and Topstep API stay here. Contains engine, execution, market (Topstep) client, observability store, CLI, debug server, and the **data bridge** (outbox + thread that sends telemetry to Railway).
- **`railway/`** — Cloud services for the G-Trade Railway project: **ingest** (FastAPI, receives bridge payloads), **analytics** (FastAPI, read-only API), **mcp** (MCP server for Cursor), **web** (Next.js). All are analytics/tooling only; no execution, no broker.
- **`docs/`** — Operator and architecture docs. Start at [docs/README.md](docs/README.md) (index). Canonical paths: [docs/architecture/overview.md](docs/architecture/overview.md), [docs/OPERATOR.md](docs/OPERATOR.md), [docs/Compliance-Boundaries.md](docs/Compliance-Boundaries.md), [docs/Current_Plan.md](docs/Current_Plan.md). Runbooks in `docs/runbooks/`; strategy/research in `docs/research/`; engineering system in `docs/engineering-system/`.
- **`.cursor/plans/`** — Execution plans. The canonical architecture and phased plan for TUI Sunset and Railway is in **tui_sunset_and_railway_data_network_6d1ff9ac.plan.md**. Do not edit the plan file unless the user explicitly asks to change the plan.

## Repositories

Code and docs live in six GitHub repos under **Zack-Grogan**:

| Repo | Contents |
|------|----------|
| **G-Trade** | This workspace: docs, .cursor, scripts, AGENTS.md, .github. "Repo root" for commands like `python scripts/onboard_openviking.py` = root of the G-Trade clone. |
| **es-hotzone-trader** | Trading CLI, engine, bridge, observability. |
| **g-trade-ingest** | Ingest API (railway/ingest). |
| **g-trade-analytics** | Analytics API (railway/analytics). |
| **g-trade-mcp** | MCP server (railway/mcp). |
| **g-trade-web** | Next.js app (railway/web). |

Branch/PR conventions apply per repo. G-Trade and es-hotzone-trader use Linear project G-Trade (team GDG) and prefix GDG where applicable.

## Major entry points

| Entry point | Location | Purpose |
|-------------|----------|---------|
| CLI | `es-hotzone-trader`: `es-trade` → `src.cli.commands:main` | Only operator surface for trading; no-arg shows help. |
| Engine | `es-hotzone-trader/src/engine/trading_engine.py` | Strategy, sync, protection, adoption, dynamic exit. |
| Bridge | `es-hotzone-trader/src/bridge/railway_bridge.py` | In-process telemetry to Railway ingest; gated by config. |
| Debug server | `es-hotzone-trader/src/server/debug_server.py` | Health and `/debug` HTTP only; no MCP. |
| Railway ingest | `railway/ingest/app.py` | POST /ingest/state, /ingest/events, /ingest/trades. |
| Railway analytics | `railway/analytics/app.py` | Read-only API over Postgres. |
| Railway MCP | `railway/mcp/app.py` | MCP endpoint for Cursor; tools backed by analytics. |
| Railway web | `railway/web/` | Next.js app; calls analytics API only. |

## Main services / modules

- **es-hotzone-trader:** `src/cli`, `src/engine`, `src/execution`, `src/market`, `src/observability`, `src/bridge`, `src/server`, `src/strategies`, `src/indicators`, `src/config`.
- **railway:** One FastAPI or Next.js app per directory (ingest, analytics, mcp, web); each has its own README and env contract.

## Dev / test / build / lint commands

| Context | Command | Notes |
|---------|---------|------|
| es-hotzone-trader | `cd es-hotzone-trader && pip install -e ".[dev]"` | Install with dev deps. |
| es-hotzone-trader | `pytest` | From repo root or es-hotzone-trader. |
| es-hotzone-trader | `ruff check .` / `black .` | Lint/format (pyproject config). |
| railway/web | `cd railway/web && npm run dev` / `npm run build` | Local dev only; deploy via Railway. |
| Docs index | `python scripts/generate_docs_index.py` | Idempotent; writes to docs/generated/. |

## Documentation contract

- **Where architecture lives:** [docs/architecture/overview.md](docs/architecture/overview.md), [docs/Architecture-Overview.md](docs/Architecture-Overview.md) (legacy alias), [docs/Current-State.md](docs/Current-State.md), [docs/OPERATOR.md](docs/OPERATOR.md).
- **When to update docs:** When you change behavior, deployment, config surface, or safety-relevant logic, update the relevant doc (OPERATOR, architecture, runbook, Compliance-Boundaries, or engineering-system) and note it in the change. For material strategy or compliance implications, add research traceability per [docs/Compliance-Boundaries.md](docs/Compliance-Boundaries.md).
- **Generated docs:** Script output under `docs/generated/` is refreshable; do not hand-edit. Authored docs under `docs/` are authoritative.

## Testing contract

- Run relevant tests before completing a change that touches code. Prefer `pytest` from the app directory; respect existing testpaths and asyncio_mode in pyproject.
- Do not remove or disable tests unless there is an explicit reason (e.g. obsolete behavior); document the reason.

## Issue / branch / PR contract

- **Linear:** All Linear issues and documents for this repo must be created in the **G-Trade** project only (team GDG). Do not use other workspace projects (e.g. grogan.trade UCML). See [docs/engineering-system/linear-setup.md](docs/engineering-system/linear-setup.md).
- **When an issue exists (e.g. Linear):** Prefer branch names that reference it (e.g. `fix/GDG-211-description`). In commits and PRs, reference the issue where applicable. See [docs/engineering-system/github-workflow.md](docs/engineering-system/github-workflow.md) and [docs/engineering-system/linear-workflow.md](docs/engineering-system/linear-workflow.md).
- **When work is exploratory:** No need to invent an issue; document findings and suggest creating an issue or plan item when formalizing.
- **PRs:** Use the repo PR template; link issue if applicable; ensure tests and docs are updated as needed.

## Safety constraints

- Do not add execution or broker logic to Railway services. Do not expose unauthenticated endpoints on ingest, analytics, MCP, or web.
- Do not refactor business logic or product architecture for the sake of the AI operating layer. Do not rename large parts of the codebase unless required for the operating layer.
- Do not add secrets or credentials to the repo. Do not assume production deployment permissions or force production automation.
- Sensitive surfaces: env files, auth config, billing, migrations, infra configs. Flag edits to these and avoid automatic destructive or broad changes.

## OpenViking resource convention

- OpenViking is used for **durable repository knowledge** (e.g. indexed docs, module maps). It is not an app runtime dependency. Cursor may query it via MCP for context; do not assume the repo depends on OpenViking at runtime.
- Prefer reading from repo docs and generated maps first; use OpenViking when the task benefits from cross-repo or durable search. See [docs/engineering-system/openviking-integration.md](docs/engineering-system/openviking-integration.md).

## What requires docs updates

- Changing CLI surface, config keys, or deployment topology.
- Adding or removing Railway services or endpoints.
- Changing compliance-relevant behavior (Topstep/CME boundaries, auth model).
- Changing test layout or entry points.

## What requires approval before editing

- Editing `.cursor/plans/tui_sunset_and_railway_data_network_6d1ff9ac.plan.md` (only when the user asks to change the plan).
- Broad refactors or product architecture changes.
- Changes to compliance or safety-critical paths (runbook, Compliance-Boundaries, execution/broker touchpoints).

## Architecture rules (do not break)

1. **Execution and Topstep stay on the Mac.** No order placement, position management, or broker API calls from Railway or any cloud service.
2. **Data flows one way: Mac → Railway.** The bridge pushes state/events/trades to the ingest API. Cloud never pushes orders or market data back to the trader.
3. **MCP runs on Railway only.** The local debug server does not expose MCP; Cursor and other MCP clients use the Railway MCP URL. Config: `server.railway_mcp_url`.
4. **Single-operator, non-commercial.** All Railway surfaces (ingest, analytics, MCP, web) use single-user auth (e.g. Bearer or allowlist). No public unauthenticated endpoints.
5. **Local trading is resilient to cloud downtime.** The bridge uses a durable outbox and fail-open behavior; trading continues if Railway is unavailable.

## Conventions

- **Python (es-hotzone-trader):** 3.11+, Click CLI, config via YAML + env. Observability in `src/observability/`, bridge in `src/bridge/`, execution in `src/execution/`, engine in `src/engine/`.
- **Railway services:** Each has a `README.md` and `requirements.txt` (or `package.json` for web). Ingest and analytics use FastAPI; MCP uses FastAPI; web uses Next.js. Auth is Bearer or single-operator token.
- **Docs:** When you change behavior or deployment, update the relevant doc (OPERATOR.md, Architecture-Overview.md, runbook, or Compliance-Boundaries.md) and, if material, add research traceability (citations/assumptions) per Compliance-Boundaries.

## What to touch

- **Code:** `es-hotzone-trader/src/`, `railway/*/` (ingest, analytics, mcp, web).
- **Config:** `es-hotzone-trader/config/default.yaml`, env vars (document in README or OPERATOR.md).
- **Docs:** `docs/*.md`, this AGENTS.md, `es-hotzone-trader/README.md`, `railway/*/README.md`, `docs/engineering-system/`, `docs/generated/` (via script only).

## What not to do

- Do not edit `.cursor/plans/tui_sunset_and_railway_data_network_6d1ff9ac.plan.md` unless the user explicitly asks to change the plan.
- Do not add execution or broker logic to Railway services.
- Do not expose unauthenticated endpoints on ingest, analytics, MCP, or web.
- Do not treat ignore files as security controls; they only reduce noise and indexing load.

## Where to go for what (routing by task)

| Task / intent | Rule(s) | Skill(s) | Doc(s) |
|---------------|---------|----------|--------|
| Structural or architecture change | 00, 20 | — | docs/architecture/overview.md, Current-State, OPERATOR |
| Issue-driven work (branch, commit, PR) | 40 | issue-to-pr | linear-workflow, github-workflow, playbook starting-work-from-linear-issue |
| Exploratory work, no issue | 05, 40 | — | cursor-operating-model, linear-workflow (exploratory) |
| Docs or generated index | 10 | — | overview (generated docs), OPERATOR |
| Railway deploy or ops | 70 | use-railway | railway-usage-policy |
| OpenViking / durable search / progress | 60, 61 | use-openviking | openviking-integration |
| Safety, destructive guard, sensitive files | 50 | — | Compliance-Boundaries, AGENTS "Safety constraints" |
| Reusing templates / global pack | 80 | — | future-project-starter, local-vs-global |

Full by-concern index: [docs/engineering-system/agent-index.md](docs/engineering-system/agent-index.md).

## Quick references

- **CLI entrypoint:** `es-trade` → `src/cli/commands.py` (`main`). No-arg shows help; no TUI.
- **Bridge:** `src/bridge/railway_bridge.py` (start/stop), `src/bridge/outbox.py` (durable queue). Gated by `observability.railway_ingest_url` and API key.
- **Debug server:** Health and `/debug` only; no MCP. `src/server/debug_server.py`.
- **Compliance:** [docs/Compliance-Boundaries.md](docs/Compliance-Boundaries.md) (Topstep, CME, pre-migration gate).
- **Engineering system:** [docs/engineering-system/overview.md](docs/engineering-system/overview.md).
