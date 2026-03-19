---
name: es-hotzone-debug
description: Debug `es-hotzone-trader` runtime, launchd service behavior, local SQLite durability, Railway bridge failures, and cross-service observability flow into ingest, analytics, MCP, and RLM. Use when the task is diagnosing trader uptime, bridge auth errors, outbox backlog, missing telemetry, or run/log recovery for this project.
---

# ES Hot-Zone Debug

Use this skill for project-specific debugging of the local trader plus Railway observability path.

## Start here

1. Prefer repo-truth over guesses:
   - Local SQLite durability via `es-trade db ...`
   - Local runtime/service state via `es-trade service ...`
   - Local log file and launchd stdout/stderr
   - Railway ingest/analytics/MCP evidence only after local state is clear
   - For `railway/web`, the live Railway URL is authoritative for Clerk-gated visibility and navigation; local standalone is for build/smoke checks, not final auth proof
2. Keep the architecture rule intact:
   - Mac executes trades
   - Railway is advisory/analytics-only
   - No recommendation should create a cloud-to-executor control path

## Primary workflow

1. Check service/runtime health.
   - `es-trade service doctor`
   - `es-trade service status`
   - `es-trade status`
2. Check local durability and backlog.
   - `es-trade db runs`
   - `es-trade db events --limit 200`
   - `es-trade db snapshots --kind state --limit 50`
   - `es-trade db bridge-health --limit 50`
   - `es-trade db logs --limit 100`
3. If bridge delivery is behind, inspect the outbox and delivery cursors through `service doctor`, then use:
   - `es-trade db replay-missing`
   - Add `--run-id <run_id>` when scoping recovery to one run
4. Correlate with Railway.
   - Ingest auth or insert failures: inspect ingest logs and `/health`
   - Analytics gaps: query runtime logs, bridge failures, and run timelines
   - MCP issues: verify MCP auth separately from internal service auth

## What to look for

- `launchd` not installed, not loaded, or writing only to stderr
- Runtime PID/status file says running but local debug endpoints are unavailable
- Outbox backlog growing while delivery cursor is flat
- Permanent auth failures (`401`, `403`, `422`) incorrectly treated as transient
- Local SQLite contains events/logs that never reached analytics
- MCP has no visibility because analytics lacks the expected runtime-log or bridge-failure records

## Recovery rules

- Prefer replay from local SQLite, not from memory and not from reconstructed prose
- Treat local observability SQLite as the source of truth
- Treat the outbox as an operational queue only
- Do not recommend deleting local durability files unless the user explicitly asks
- Do not recommend restarting the trader before collecting local SQLite and log evidence

## Output expectations

When using this skill, report:

1. Local runtime state
2. Local durability state
3. Bridge/auth state
4. Railway visibility state, including the live Railway URL when web auth or navigation is involved
5. Exact recovery action taken or recommended
