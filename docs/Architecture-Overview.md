# Architecture Overview — local trader repo

**Canonical path:** [docs/architecture/overview.md](architecture/overview.md). This file is kept for compatibility.

## One-line summary

**Execution, observability, broker truth, and operator tooling stay on the Mac.** The active stack is Python + CLI + Flask + SQLite + Topstep.

## What runs where

| Where | What |
|-------|------|
| **Local (Mac)** | Trading engine, order executor, Topstep client, launchd wrapper, Flask console, SQLite observability store, trade review, regime analysis, and all operator workflows. |
| **Archive only** | Retired Railway and MCP stack. Historical notes live under `docs/archive/railway-sunset/`. |

## Active data flow

- **Market and broker state:** Topstep client → local trading engine
- **Observability:** engine/execution/runtime → local SQLite
- **Operator visibility:** CLI and local Flask console read from local runtime state and SQLite
- **Cloud dependency:** none required for trading or debugging

## Active modules

| Module | Purpose |
|--------|---------|
| `src/cli/` | Operator commands and launchd workflow |
| `src/engine/` | Strategy, regime logic, session gating, exits |
| `src/execution/` | Order execution, protection, reconciliation |
| `src/market/` | Topstep client, broker truth, fills/orders/positions |
| `src/observability/` | SQLite durability, runtime logs, decision snapshots, trade review data |
| `src/server/` | Local Flask console, SSE feeds, `/health`, `/debug` |
| `src/analysis/` | Regime packet and trade-review analysis |

## Key docs

- [docs/README.md](README.md)
- [OPERATOR.md](OPERATOR.md)
- [Current-State.md](Current-State.md)
- [Tasks.md](Tasks.md)
- [Compliance-Boundaries.md](Compliance-Boundaries.md)
- [archive/railway-sunset/README.md](archive/railway-sunset/README.md)
