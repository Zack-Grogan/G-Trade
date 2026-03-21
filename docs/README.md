# G-Trade documentation

Start here to understand the current system. The active operator surfaces are the **CLI** and **local SQLite** observability. Execution, Topstep access, observability, and debugging all run on the Mac.

## Current state

- **Local-first stack:** `es-hotzone-trader` is the active product. It owns execution, broker truth, SQLite durability, trade review, logs, and the local console.
- **No cloud dependency:** Railway and MCP were retired from the active workflow. Historical notes remain archived only.
- **Launch-readiness gate:** Live-mode checks are fail-closed and require explicit funded-account, broker-truth, and recovery proof before the launch summary can turn green.

Full architecture and rationale: [Architecture-Overview.md](Architecture-Overview.md).

## Docs to read first

| Doc | Purpose |
|-----|--------|
| [architecture/overview.md](architecture/overview.md) | What runs where, data flow, active modules, local-only architecture. |
| [OPERATOR.md](OPERATOR.md) | CLI commands, launchd workflow, compliance. |
| [Observability-Contract.md](Observability-Contract.md) | Logging streams, SQLite taxonomy, decision IDs, and operator queries. |
| [Current-State.md](Current-State.md) | What is operational, validated, and not done. |
| [Tasks.md](Tasks.md) | Checklist of trader tasks and hardening work. |
| [Compliance-Boundaries.md](Compliance-Boundaries.md) | Topstep/CME boundaries and compliance gate. |
| [risk/topstep-evaluation-mirror.md](risk/topstep-evaluation-mirror.md) | Optional local trailing-drawdown mirror vs Topstep rules (citations + limits). |
| [replay/replay-topstep-deprecated.md](replay/replay-topstep-deprecated.md) | **`replay-topstep` is deprecated** — bar-only historical replay is not validated research; prefer tape replay. |
| [runbooks/ES Hot Zone Trader Live Restart Runbook.md](runbooks/ES%20Hot%20Zone%20Trader%20Live%20Restart%20Runbook.md) | Stop/restart, state reset (retained for future upgrades). |
| [engineering-system/overview.md](engineering-system/overview.md) | AI operating layer, workflow, and generated docs. |
| [archive/railway-sunset/README.md](archive/railway-sunset/README.md) | Historical record of the retired Railway stack. |

**Broker / Topstep API (reference):** [TopStepX / ProjectX Gateway API](TopStepX/README.md) — REST and SignalR endpoints for `api.topstepx.com` / `rtc.topstepx.com` (mirrors [ProjectX Gateway docs](https://gateway.docs.projectx.com/docs/intro) with TopStepX URLs).

Legacy alias: [Architecture-Overview.md](Architecture-Overview.md) (points to architecture/overview.md).

## Runbooks

Procedures for operators (restart, state reset, forensics):

- [ES Hot Zone Trader Live Restart Runbook](runbooks/ES%20Hot%20Zone%20Trader%20Live%20Restart%20Runbook.md)
- [Project onboarding: Linear](runbooks/Project-onboarding-Linear.md) — first-time setup for Linear (issues, MCP) and generated docs refresh.

## Research and strategy

- **[strategy.md](strategy.md)** — Trading-oriented description of the hot-zone matrix, vetoes, regime, risk, and execution (with code pointers and external references).
- **[strategy-research.md](strategy-research.md)** — Research-first audit of the current gate stack, with literature review, evidence-strength calls, and next-step recommendations.

The files in **[research/](research/)** are strategy, framework, and research material, not operator/runbook docs. They describe concepts like regime labeling, hot zones, order flow, and evaluation methods that inform the local trader.

- [research/](research/) — Algos General, Mixture-of-Experts, Regime Labeling, Hotzones, Dataset Schema, and related strategy/framework docs.
- [research/main-vs-cli-trading-policy.md](research/main-vs-cli-trading-policy.md) — **`main` vs `cli`** engine/policy drift, outcome effects, and **config recipe** to approximate the old setup while keeping Pre-Open `zone_weights`.
