# Compliance Boundaries — TUI Sunset and Railway Data Network

This document records the compliance boundaries for the CLI-only local surface and Railway-backed analytics. The TUI Sunset and Railway migration is complete; the gate below applies to any future major runtime or deployment changes. For architecture context, see [Architecture-Overview.md](Architecture-Overview.md).

## Topstep

- **Source:** [Topstep Terms of Use](https://www.topstep.com/terms-of-use/)
- **Boundary:** Execution, Topstep API calls, and live market/order streams **remain on the Mac only**. No execution from cloud; no VPN/VPS for the trading account.
- **What we do:** All order placement, position management, market data consumption for trading, and Topstep API usage run in the local `es-trade start` process. Railway services are analytics and tooling only: ingest (receive telemetry), Postgres (store), analytics API (read-only), MCP (read-only tools/resources), Next.js (read-only UI). No broker connection and no order flow from Railway.

## CME / Market Data

- **Source:** [CME Market Data Licensing](https://www.cmegroup.com/market-data/license-data.html)
- **Boundary:** Raw market data may be sent to cloud only for personal use: private scope, no redistribution, with retention and access controls. Compliance and licensing remain the operator’s responsibility.
- **What we do:** If raw market data is sent to Railway (e.g. for analytics), it is stored in a private schema with access limited to the single-operator auth model, no redistribution, and retention/schema separation as defined in the architecture. Operator is responsible for ensuring use complies with CME and any other data licenses.

## Compliance Gate (for major changes)

Before making major runtime or deployment changes (e.g. changing execution path or cloud scope):

- [ ] Trader is **stopped** (`es-trade stop`). No live trading during the change.
- [ ] Operator has read and acknowledged Topstep boundary: execution stays on Mac; no execution from Railway.
- [ ] Operator has read and acknowledged CME/data boundary: any cloud data use is personal, private, no redistribution; operator responsible for licensing.
- [ ] No unresolved entry or stuck state; runbook for state reset has been reviewed (see [runbooks/ES Hot Zone Trader Live Restart Runbook](runbooks/ES%20Hot%20Zone%20Trader%20Live%20Restart%20Runbook.md) — section "State reset and compliance").

Once all items are checked, the change may proceed. Re-check if scope or deployment model changes.

## Research traceability

Material architecture or strategy changes in this repo should include citations and assumption notes in docs or PRs (e.g. Topstep/CME references above, and any strategy or risk logic that relies on published research).
