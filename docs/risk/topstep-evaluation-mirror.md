# Topstep evaluation risk mirror (local approximation)

This document defines how the **optional** `evaluation_drawdown_mirror` mode in [`RiskConfig`](../../src/config/loader.py) relates to Topstep’s published rules, and what the codebase **does not** guarantee.

## Official sources (verify before relying on this mode)

- [Topstep Terms of Use](https://www.topstep.com/terms-of-use/) — binding account rules.
- [Topstep Help Center — TopstepX™ Trailing Personal Daily Loss Limit](https://help.topstep.com/en/articles/10490293-topstepx-trailing-personal-daily-loss-limit) — product-specific loss mechanics (wording and thresholds change; read the live article).
- Topstep marketing/educational pages (e.g. blog posts on drawdown) are **secondary**; use them for intuition only.

## What the bot already enforced (unchanged)

- **Daily loss / circuit breakers** in [`RiskManager.can_trade`](../../src/engine/risk_manager.py) use **`_daily_pnl`** from **closed trades** in the configured session window, not a full broker evaluation-equity model.
- **Per-position flatten** uses unrealized P&amp;L against `max_position_loss` and other gates in `should_flatten_position`.

## What the optional mirror adds

When `risk.evaluation_drawdown_mirror_enabled` is `true`, the risk manager maintains:

1. **`evaluation_starting_equity`** — nominal account equity at **process start** (you should align this with the Topstep dashboard when you start the bot).
2. **`_mirror_session_realized_pnl`** — sum of **closed-trade P&amp;L** since the risk manager was reset (replay session or `reset_state`), **not** reset on the intraday session date rollover that clears `_daily_pnl`.
3. **Unrealized P&amp;L** on the open position (same ES $50/point convention as elsewhere in [`RiskManager`](../../src/engine/risk_manager.py)).
4. **High water mark (HWM)** of **equity proxy** = `starting + session_realized + unrealized`, updated on each mirror refresh.
5. **Trailing floor** = `HWM - evaluation_trailing_drawdown_dollars`.
6. **Stop line** = `floor + evaluation_mirror_buffer_dollars` — when equity proxy **≤ stop line**, the mirror **latches** `evaluation_drawdown_mirror`, blocks new entries, and requests flatten while a position is open.

This is a **conservative operational guard**, not a certified replication of Topstep’s internal calculations (which may use balances, fees, instruments, or timing you do not model here).

## What we do **not** approximate

- Exact **trailing maximum drawdown** semantics for every Topstep product tier (combine vs funded, X vs legacy, etc.).
- **Overnight / cross-session** handling beyond your choice of `evaluation_starting_equity` at startup.
- **Fees, commissions, or non-ES instruments** in the equity proxy.
- **Broker-side liquidation** timing or partial fills.

## Operator checklist

1. Confirm the rule text for **your** account type on Topstep’s site.
2. Set `evaluation_starting_equity` to **current account equity** when starting the trader (or accept drift).
3. Set `evaluation_trailing_drawdown_dollars` and `evaluation_mirror_buffer_dollars` to match your **comfort margin** relative to the official limit (buffer is dollars **above** the raw trailing floor for early flatten).
4. Treat breach events in SQLite (`evaluation_drawdown_mirror`) as **stop trading / flatten** signals; confirm on the Topstep dashboard.

## Related docs

- [`docs/Compliance-Boundaries.md`](../Compliance-Boundaries.md) — execution locality and compliance gate.
- [`docs/OPERATOR.md`](../OPERATOR.md) — emergency halt and runtime procedures.
