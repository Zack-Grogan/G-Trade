# Compliance Boundaries

This document records the compliance boundaries for the current local trader stack. The gate below applies to any future major runtime or deployment changes.

## Topstep

- **Source:** [Topstep Terms of Use](https://www.topstep.com/terms-of-use/)
- **Boundary:** Execution, Topstep API calls, and live market/order streams **remain on the Mac only**. No execution from cloud; no VPN/VPS for the trading account.
- **What we do:** All order placement, position management, market data consumption for trading, and Topstep API usage run in the local `es-trade start` process.
- **Evaluation risk (optional):** An approximate trailing-drawdown mirror is documented in [risk/topstep-evaluation-mirror.md](risk/topstep-evaluation-mirror.md); it is **not** a certified copy of Topstep’s internal calculations.

## CME / Market Data

- **Source:** [CME Market Data Licensing](https://www.cmegroup.com/market-data/license-data.html)
- **Boundary:** Market data usage must remain personal, private, and non-redistributed. Compliance and licensing remain the operator’s responsibility.
- **What we do:** The active system keeps trading data local. Operator remains responsible for any future external storage or redistribution decisions.

## Compliance Gate (for major changes)

Before making major runtime or deployment changes (e.g. changing execution path or cloud scope):

- [ ] Trader is **stopped** (`es-trade stop`). No live trading during the change.
- [ ] Operator has read and acknowledged Topstep boundary: execution stays on Mac.
- [ ] Operator has read and acknowledged CME/data boundary: any cloud data use is personal, private, no redistribution; operator responsible for licensing.
- [ ] No unresolved entry or stuck state; runbook for state reset has been reviewed (see [runbooks/ES Hot Zone Trader Live Restart Runbook](runbooks/ES%20Hot%20Zone%20Trader%20Live%20Restart%20Runbook.md) — section "State reset and compliance").

Once all items are checked, the change may proceed. Re-check if scope or deployment model changes.

## Research traceability

Material architecture or strategy changes in this repo should include citations and assumption notes in docs or PRs (e.g. Topstep/CME references above, and any strategy or risk logic that relies on published research).
