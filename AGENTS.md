# Agent guide — G-Trade / es-hotzone-trader

This file is the **repository operating contract** for AI agents. Read it before structural or behavioral changes. It orients agents to architecture, layout, conventions, and guardrails.

**What this document is:** A **router and gate-keeper**. It tells you which rule, skill, or doc to load for a given intent. It does not explain how Railway works, how to write Python, or how external APIs behave — those live in skills and official docs.

**What this document is NOT:** A code reference or a substitute for reading the referenced skill or doc. If you need more than "which gate do I hit", load the referenced skill/doc; do not infer from AGENTS.md alone.

**Heuristic: Verify before implement.** For any external API, SDK, or CLI command you have not personally verified in the last 30 days, treat it as potentially stale. Use web search, official docs, or an MCP tool to confirm. Do not guess from training data — e.g. do not spend many messages guessing Railway CLI behavior; read [.cursor/skills/use-railway/SKILL.md](.cursor/skills/use-railway/SKILL.md) first.

## Repo purpose

G-Trade is a workspace containing:

- **es-hotzone-trader:** CLI-based ES hot-zone day trading system. Execution and Topstep API run on the host (Mac). The primary operator surfaces are the CLI and the local Flask console.
- **railway/:** Legacy cloud services for the G-Trade Railway project (ingest, analytics, MCP, web). Analytics/tooling only; not required for the current local Sunday/Monday launch cut.

Human-maintained docs are the source of truth. Generated docs (e.g. from `scripts/generate_docs_index.py`) are machine-maintained indexes; do not treat them as overriding architecture or operator docs.

## Project layout

- **`es-hotzone-trader/`** — Local trading system (Python). Execution and Topstep API stay here. Contains engine, execution, market (Topstep) client, observability store, CLI, local Flask console, and the optional legacy **data bridge** (outbox + thread that can send telemetry to Railway when explicitly enabled).
- **`railway/`** — Legacy cloud services for the G-Trade Railway project: **ingest** (FastAPI), **analytics** (FastAPI), **mcp** (MCP server), **web** (Next.js). These remain analytics/tooling only; no execution, no broker.
- **`docs/`** — Operator and architecture docs. Start at [docs/README.md](docs/README.md) (index). Canonical paths: [docs/architecture/overview.md](docs/architecture/overview.md), [docs/OPERATOR.md](docs/OPERATOR.md), [docs/Compliance-Boundaries.md](docs/Compliance-Boundaries.md), [docs/Current_Plan.md](docs/Current_Plan.md). Runbooks in `docs/runbooks/`; strategy/research in `docs/research/`; engineering system in `docs/engineering-system/`.
- **`.cursor/plans/`** — Execution plans. The canonical architecture and phased plan for TUI Sunset and Railway is in **tui_sunset_and_railway_data_network_6d1ff9ac.plan.md**. Do not edit the plan file unless the user explicitly asks to change the plan.

## Repository ownership

`G-Trade` is now the canonical monorepo. The root repository owns:

- `es-hotzone-trader/`
- `railway/ingest/`
- `railway/analytics/`
- `railway/mcp/`
- `railway/web/`
- root docs, scripts, `.cursor/`, `.codex/`, and `.github/`

The previous standalone GitHub repositories remain historical references only. Their import remotes and SHAs are recorded in [docs/archive/repository-imports-2026-03-19.md](docs/archive/repository-imports-2026-03-19.md).

Branch/PR conventions now apply at the root monorepo level unless the user explicitly asks for a historical repo workflow.

## Major entry points

| Entry point | Location | Purpose |
|-------------|----------|---------|
| CLI | `es-hotzone-trader`: `es-trade` → `src.cli.commands:main` | Only operator surface for trading; no-arg shows help. |
| Engine | `es-hotzone-trader/src/engine/trading_engine.py` | Strategy, sync, protection, adoption, dynamic exit. |
| Local console | `es-hotzone-trader/src/server/flask_console.py` | Local Flask operator console with `/`, `/chart`, `/trades`, `/logs`, `/system`, plus `/health` and `/debug` JSON. |
| Bridge | `es-hotzone-trader/src/bridge/railway_bridge.py` | Optional legacy telemetry path to Railway ingest; disabled by default for the current launch posture. |
| Railway ingest | `railway/ingest/app.py` | Legacy optional ingest API for bridged telemetry. |
| Railway analytics | `railway/analytics/app.py` | Legacy optional read-only API over Postgres. |
| Railway MCP | `railway/mcp/app.py` | Legacy optional MCP endpoint backed by analytics. |
| Railway web | `railway/web/` | Legacy optional cloud operator console. |

## Main services / modules

- **es-hotzone-trader:** `src/cli`, `src/engine`, `src/execution`, `src/market`, `src/observability`, `src/bridge`, `src/server`, `src/strategies`, `src/indicators`, `src/config`.
- **railway:** One FastAPI or Next.js app per directory (ingest, analytics, mcp, web); each has its own README and env contract.

## Dev / test / build / lint commands

| Context | Command | Notes |
|---------|---------|------|
| es-hotzone-trader | `cd es-hotzone-trader && pip install -e ".[dev]"` | Install with dev deps. |
| es-hotzone-trader | `pytest` | From repo root or es-hotzone-trader. |
| es-hotzone-trader | `ruff check .` / `black .` | Lint/format (pyproject config). |
| railway/web | `cd railway/web && bun run dev` / `bun run build` | Bun; local dev only; deploy via Railway. |
| Docs index | `python scripts/generate_docs_index.py` | Idempotent; writes to docs/generated/. |

## Documentation contract

- **Where architecture lives:** [docs/architecture/overview.md](docs/architecture/overview.md), [docs/Architecture-Overview.md](docs/Architecture-Overview.md) (legacy alias), [docs/Current-State.md](docs/Current-State.md), [docs/OPERATOR.md](docs/OPERATOR.md).
- **When to update docs:** When you change behavior, deployment, config surface, or safety-relevant logic, update the relevant doc (OPERATOR, architecture, runbook, Compliance-Boundaries, or engineering-system) and note it in the change. For material strategy or compliance implications, add research traceability per [docs/Compliance-Boundaries.md](docs/Compliance-Boundaries.md).
- **Generated docs:** Script output under `docs/generated/` is refreshable; do not hand-edit. Authored docs under `docs/` are authoritative.

## Testing contract

- Run relevant tests before completing a change that touches code. Prefer `pytest` from the app directory; respect existing testpaths and asyncio_mode in pyproject.
- Do not remove or disable tests unless there is an explicit reason (e.g. obsolete behavior); document the reason.
- For Clerk-gated `railway/web` changes, treat the deployed Railway URL as the authoritative environment. Local `bun run dev` or `bun run start` is useful for build and smoke checks, but final auth gating, navigation, and data-visibility validation must happen on the live Railway deployment after push.

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
2. **Local SQLite is authoritative.** If the legacy bridge is enabled, data still flows one way: Mac → Railway. Cloud never pushes orders or market data back to the trader.
3. **The local Flask console is the primary browser-based operator surface.** The local server exposes `/health`, `/debug`, and local console pages; it does not expose MCP.
4. **Railway is optional legacy infrastructure.** If used, all Railway surfaces remain single-operator and non-execution.
5. **Local trading must remain viable with bridge disabled.** The current launch posture assumes no required cloud dependency for operator workflows.

## Conventions

- **Python (es-hotzone-trader):** 3.11+, Click CLI, config via YAML + env. Observability in `src/observability/`, bridge in `src/bridge/`, execution in `src/execution/`, engine in `src/engine/`.
- **Railway services:** Each has a `README.md` and `requirements.txt` (or `package.json` for web). Ingest, analytics, MCP, and RLM use FastAPI; web uses Next.js. Auth is Bearer or single-operator token.
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

## Available tools (MCP + CLI + Skill)

| Tool | Access | Use for |
|------|--------|---------|
| Railway MCP + CLI | [.cursor/skills/use-railway/SKILL.md](.cursor/skills/use-railway/SKILL.md) | Railway: deploys, logs, status, variables, environments, buckets, domains. Read skill first; run preflight before any mutation. |
| Upstash skill | [.cursor/skills/upstash/SKILL.md](.cursor/skills/upstash/SKILL.md) | Redis, QStash, rate limit, workflow, vector, search. Route to sub-skill; do not hand-roll clients. |
| Exa MCP | `web_search_exa`, `get_code_context_exa` | Web/code search — use before guessing external API or SDK behavior. |
| OpenViking MCP | [.cursor/skills/use-openviking/SKILL.md](.cursor/skills/use-openviking/SKILL.md) | Cross-repo durable knowledge, semantic search, progress reports. |
| Linear MCP | Linear tools | Issues, projects, team workflow. |
| G-Trade MCP | `g_trade` | Trading runs, events, performance, execution state. |
| GitHub MCP | GitHub tools | Repos, PRs, issues. |
| Playwright MCP | Playwright tools | Browser automation. |
| Clerk MCP | Clerk tools | Auth/user management. |

Prefer MCP and CLIs over asking for API keys or writing one-off scripts (rule 15).

## Subagent routing

The GLM orchestrates by dispatching to specialized subagents; dispatch is execution, not delegation. See [.cursor/rules/03-orchestration-first.mdc](.cursor/rules/03-orchestration-first.mdc) for the full model.

| Task type | Subagent | When to use |
|-----------|----------|-------------|
| Exploration / broad search | **explore** | Find files by pattern, search code for keywords, "how does X work" across codebase. Specify thoroughness (quick / medium / very thorough). |
| Code review | **code-reviewer** | PR or diff review; correctness, security, maintainability. |
| API / endpoint testing | **api-tester** | API validation, performance testing, QA. |
| Quality / verification | **evidence-collector** | QA with visual evidence; default to finding issues. |
| Performance analysis | **performance-benchmarker** | Measure, analyze, improve performance. |
| Documentation | **technical-writer** | Developer docs, API refs, READMEs, tutorials. |
| Security review | **security-engineer** | Threat modeling, vulnerability assessment, secure code review. |
| Status / progress / analysis | **openviking-analyst** | Project status, impact analysis, cross-doc synthesis (with OpenViking). |
| Shell / commands | **shell** | Git, Railway CLI, tests, any terminal execution. |
| Multi-step research or execution | **generalPurpose** | Broad research or multi-step work when no single specialist fits. |

**Dispatch patterns:** Run at most **two subagents at a time**. Parallel (max 2) for independent subtasks; sequential for dependent work (e.g. implement → review → test). For full spec-to-production pipeline, apply the **agents-orchestrator** skill (.cursor/skills/agents-orchestrator/).

## Where to go for what (forced gates)

These gates are binding: when intent matches a row below, do the listed step before proceeding. You **MUST** do the "Must do first" step before anything else. Do not do the "Do not do" anti-patterns.

| Gate | Intent matches | Must do first | Do not do |
|------|----------------|---------------|-----------|
| **Railway operations** | Railway deploy, logs, status, variables, environment, service, bucket, domain, networking | **Read [.cursor/skills/use-railway/SKILL.md](.cursor/skills/use-railway/SKILL.md) first.** Run preflight: `railway whoami --json` and `railway status --json`. Prefer GitHub push for deploys; use Railway MCP when available; use CLI only when MCP isn't working or the resource isn't natively available. Also apply rule 70 when planning or operating Railway. | Do not guess CLI auth state; do not fall back to raw GraphQL without reading the skill's `request.md` reference; when using CLI for a deploy, do not push to GitHub in the same iteration (one build path). |
| **Upstash / serverless data** | Redis, QStash, rate limit, workflow, vector, search | **Read [.cursor/skills/upstash/SKILL.md](.cursor/skills/upstash/SKILL.md) first.** Route to the matching sub-skill. | Do not hand-roll HTTP clients; do not invent env var names without checking the skill. |
| **External SDK / API (non-Railway)** | Daytona, LangChain, x.ai, any Python/JS package not already in the repo | **Read [.cursor/rules/92-research-and-official-sdks.mdc](.cursor/rules/92-research-and-official-sdks.mdc) first.** Web search or doc fetch before implementing. | Do not guess import paths; do not use training data for API shapes. |
| **Third-party / BaaS** | Any framework, BaaS, or external service | **Read [.cursor/rules/90-third-party-baas-research.mdc](.cursor/rules/90-third-party-baas-research.mdc) first.** Confirm from official docs (current date). | Do not assume from training data. |
| **Repo / project-wide search** | "How does X work", "where is Y", cross-repo context, durable knowledge | **Read [.cursor/skills/use-openviking/SKILL.md](.cursor/skills/use-openviking/SKILL.md) first.** | Do not guess; do not substitute raw grep when OpenViking is the right tool for cross-repo. |
| **Status / progress / analysis** | "Progress monster", impact, project status, deep analysis | **Read rule 61.** Apply use-openviking skill; consider openviking-analyst subagent. | Do not synthesize from partial in-repo grep. |
| **Railway iteration (fixing a deploy)** | Build failing, service crashing, investigating logs | **Read [.cursor/rules/71-railway-iteration-single-build-path.mdc](.cursor/rules/71-railway-iteration-single-build-path.mdc).** Prefer GitHub push; use CLI only when MCP unavailable or operation not in MCP. | — |
| **New integration / adapter** | Writing new integration, adapter, or service module | Read the relevant skill first; if none exists, verify SDK/API from official docs before coding. | Do not write integration code without verifying SDK/API shape first. |
| **Structural or architecture change** | Module boundaries, config surface, deployment topology | 00, 20. Read docs/architecture/overview.md, Current-State, OPERATOR. | — |
| **Issue-driven work (branch, commit, PR)** | Linear issue, branch, PR | 40. Use issue-to-pr skill; linear-workflow, github-workflow. | — |
| **Exploratory work, no issue** | No Linear issue yet | 05, 40. cursor-operating-model, linear-workflow (exploratory). | — |
| **Docs or generated index** | Updating or generating docs | 10. overview (generated docs), OPERATOR. | — |
| **Safety, destructive guard, sensitive files** | Env files, auth, billing, migrations | 50. Compliance-Boundaries, AGENTS "Safety constraints". | — |
| **Reusing templates / global pack** | Future-project-starter, local-vs-global | 80. future-project-starter, local-vs-global. | — |

Full by-concern index: [docs/engineering-system/agent-index.md](docs/engineering-system/agent-index.md).

## Quick references

- **CLI entrypoint:** `es-trade` → `src/cli/commands.py` (`main`). No-arg shows help; no TUI.
- **Bridge:** `src/bridge/railway_bridge.py` (start/stop), `src/bridge/outbox.py` (durable queue). Legacy/optional; gated by `observability.railway_ingest_url` and preferred `observability.internal_api_token` / `GTRADE_INTERNAL_API_TOKEN`.
- **Local console:** `src/server/flask_console.py` via `src/server/debug_server.py` compatibility wrapper. Browser pages plus `/health` and `/debug`; no MCP.
- **Compliance:** [docs/Compliance-Boundaries.md](docs/Compliance-Boundaries.md) (Topstep, CME, pre-migration gate).
- **Engineering system:** [docs/engineering-system/overview.md](docs/engineering-system/overview.md).
