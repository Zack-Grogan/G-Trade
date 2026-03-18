# G-Trade documentation

Start here to understand the system. The operator interface is **CLI-only** (no TUI). Execution and Topstep run on the Mac; telemetry goes one-way to Railway for analytics and MCP.

## Current state

- **Migration completed:** TUI was removed; CLI is the only local operator surface. The data bridge sends state, events, and trades to Railway (Postgres, ingest, analytics, MCP, Next.js). MCP runs on Railway so Cursor can inspect runs and state without the local process.
- **Execution:** All order flow and Topstep API stay on the Mac. Railway is analytics and tooling only; it never sends orders or market data back.

Full architecture and rationale: [Architecture-Overview.md](Architecture-Overview.md). Completed execution plan: [.cursor/plans/tui_sunset_and_railway_data_network_6d1ff9ac.plan.md](../.cursor/plans/tui_sunset_and_railway_data_network_6d1ff9ac.plan.md).

## Docs to read first

| Doc | Purpose |
|-----|--------|
| [architecture/overview.md](architecture/overview.md) | What runs where (Mac vs Railway), data flow, services, config (canonical). |
| [OPERATOR.md](OPERATOR.md) | CLI commands, MCP setup, Railway/bridge config, compliance. |
| [Current-State.md](Current-State.md) | What is operational, validated, and not done. |
| [Tasks.md](Tasks.md) | Checklist of migration tasks (completed and open). |
| [Compliance-Boundaries.md](Compliance-Boundaries.md) | Topstep/CME boundaries and compliance gate. |
| [runbooks/ES Hot Zone Trader Live Restart Runbook.md](runbooks/ES%20Hot%20Zone%20Trader%20Live%20Restart%20Runbook.md) | Stop/restart, state reset (retained for future upgrades). |
| [engineering-system/overview.md](engineering-system/overview.md) | AI operating layer, workflow, and generated docs. |

Legacy alias: [Architecture-Overview.md](Architecture-Overview.md) (points to architecture/overview.md).

## Runbooks

Procedures for operators (restart, state reset, forensics):

- [ES Hot Zone Trader Live Restart Runbook](runbooks/ES%20Hot%20Zone%20Trader%20Live%20Restart%20Runbook.md)
- [Project onboarding: Linear and OpenViking](runbooks/Project-onboarding-Linear-and-OpenViking.md) — first-time setup for Linear (issues, MCP) and OpenViking (ingest).

## Research and strategy

The files in **[research/](research/)** are strategy, framework, and research material—not the operator interface or deployment docs. They describe concepts (e.g. regime labeling, mixture-of-experts, hot zones, order flow) and dataset/schema ideas. The live system is CLI + Railway as above; these docs are reference for how the strategy and research are designed.

- [research/](research/) — Algos General, Mixture-of-Experts, Regime Labeling, Hotzones, Dataset Schema, and related strategy/framework docs.
