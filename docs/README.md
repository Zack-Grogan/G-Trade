# G-Trade documentation

Start here to understand the current system. The active operator surfaces are the **CLI** and the **local Flask console**. Execution, Topstep access, observability, and debugging all run on the Mac.

## Current state

- **Local-first stack:** `es-hotzone-trader` is the active product. It owns execution, broker truth, SQLite durability, trade review, logs, and the local console.
- **No cloud dependency:** Railway and MCP were retired from the active workflow. Historical notes remain archived only.

Full architecture and rationale: [Architecture-Overview.md](Architecture-Overview.md).

## Docs to read first

| Doc | Purpose |
|-----|--------|
| [architecture/overview.md](architecture/overview.md) | What runs where, data flow, active modules, local-only architecture. |
| [OPERATOR.md](OPERATOR.md) | CLI commands, local console, launchd workflow, compliance. |
| [Current-State.md](Current-State.md) | What is operational, validated, and not done. |
| [Tasks.md](Tasks.md) | Checklist of trader tasks and hardening work. |
| [Compliance-Boundaries.md](Compliance-Boundaries.md) | Topstep/CME boundaries and compliance gate. |
| [runbooks/ES Hot Zone Trader Live Restart Runbook.md](runbooks/ES%20Hot%20Zone%20Trader%20Live%20Restart%20Runbook.md) | Stop/restart, state reset (retained for future upgrades). |
| [engineering-system/overview.md](engineering-system/overview.md) | AI operating layer, workflow, and generated docs. |
| [archive/railway-sunset/README.md](archive/railway-sunset/README.md) | Historical record of the retired Railway stack. |

Legacy alias: [Architecture-Overview.md](Architecture-Overview.md) (points to architecture/overview.md).

## Runbooks

Procedures for operators (restart, state reset, forensics):

- [ES Hot Zone Trader Live Restart Runbook](runbooks/ES%20Hot%20Zone%20Trader%20Live%20Restart%20Runbook.md)
- [Project onboarding: Linear and OpenViking](runbooks/Project-onboarding-Linear-and-OpenViking.md) — first-time setup for Linear (issues, MCP) and OpenViking (ingest).

## Research and strategy

The files in **[research/](research/)** are strategy, framework, and research material, not operator/runbook docs. They describe concepts like regime labeling, hot zones, order flow, and evaluation methods that inform the local trader.

- [research/](research/) — Algos General, Mixture-of-Experts, Regime Labeling, Hotzones, Dataset Schema, and related strategy/framework docs.
