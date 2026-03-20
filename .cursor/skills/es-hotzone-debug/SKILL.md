---
name: es-hotzone-debug
description: Debug `es-hotzone-trader` runtime, launchd service behavior, local SQLite durability, CLI/runtime inspection issues, broker truth mismatches, and run/log recovery for this project.
---

# ES Hot-Zone Debug

Use this skill for project-specific debugging of the local trader and its local operator surfaces.

## Start here

1. Prefer repo-truth over guesses:
   - Local SQLite durability via `es-trade db ...`
   - Local runtime/service state via `es-trade service ...`
   - Local log file and launchd stdout/stderr
   - `es-trade status` / `es-trade debug` after local runtime and SQLite are clear
2. Keep the architecture rule intact:
   - Mac executes trades
   - SQLite is authoritative
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
3. If local state and broker truth disagree, inspect:
   - `es-trade broker-truth`
   - `es-trade analyze trade-review`
   - `es-trade debug` and `logs/runtime/runtime_status.json`

## What to look for

- `launchd` not installed, not loaded, or writing only to stderr
- Runtime PID/status file says running but `es-trade debug` or SQLite snapshots look stale
- Local position and broker position disagree
- CLI status/debug is stale or missing data relative to SQLite snapshots
- Runtime logs are noisy, missing, or unreadable
- SQLite contains state the CLI is not surfacing correctly

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
4. CLI / SQLite visibility state
5. Exact recovery action taken or recommended
