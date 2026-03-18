# Current state and plan reference

**This repo is in steady state after the TUI Sunset and Railway migration.** There is no active multi-phase “plan” document here; the architecture is fixed and the migration is complete.

## Current system

- **Operator interface:** CLI only (`es-trade start | stop | restart | status | debug | events | …`). No TUI.
- **Execution:** Trading engine, order executor, and Topstep API run on the Mac only.
- **Telemetry:** In-process bridge sends state, events, and trades one-way to Railway (Postgres, ingest, analytics, MCP, Next.js). MCP runs on Railway so Cursor can inspect runs without the local process.
- **Railway:** Analytics and tooling only; no execution, no orders, no market data from cloud.

## Where to look

- **Architecture and daily use:** [docs/README.md](README.md) (index), [Architecture-Overview.md](Architecture-Overview.md), [OPERATOR.md](OPERATOR.md).
- **Operational state and tasks:** [Current-State.md](Current-State.md) (what's done/validated), [Tasks.md](Tasks.md) (checklist).
- **Completed migration plan (what we did):** [.cursor/plans/tui_sunset_and_railway_data_network_6d1ff9ac.plan.md](../.cursor/plans/tui_sunset_and_railway_data_network_6d1ff9ac.plan.md).
- **Runbooks and compliance:** [runbooks/ES Hot Zone Trader Live Restart Runbook.md](runbooks/ES%20Hot%20Zone%20Trader%20Live%20Restart%20Runbook.md), [Compliance-Boundaries.md](Compliance-Boundaries.md).
- **Strategy and research (reference only):** [research/](research/).

Future work (e.g. new features or ops changes) should be tracked in Linear or new plan files as needed, not in this file.
