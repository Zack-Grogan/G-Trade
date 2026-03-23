# TopStepX (ProjectX Gateway API)

This folder documents the **TopStepX** REST and realtime APIs. The underlying **ProjectX Gateway API** is shared across platforms (for example **The Futures Desk** and **TopStepX**). Official upstream docs live at [ProjectX Gateway API Documentation](https://gateway.docs.projectx.com/docs/intro); examples there may use another host—**this repo’s copy uses TopStepX URLs** for local integration work.

## Base URLs (TopStepX)

| Surface | URL |
|--------|-----|
| REST API | `https://api.topstepx.com` |
| User hub (SignalR) | `https://rtc.topstepx.com/hubs/user` |
| Market hub (SignalR) | `https://rtc.topstepx.com/hubs/market` |

**Swagger UI:** `https://api.topstepx.com/swagger/index.html`

## Getting started

- [Introduction](getting-started/introduction.md)
- [Authentication](getting-started/authentication.md) — API key, authorized applications, session validation
- [Placing your first order](getting-started/first-order.md)
- [Connection URLs](getting-started/connection-urls.md)
- [Rate limits](getting-started/rate-limits.md)

## API reference

### Account

- [Search for accounts](api-reference/account/search.md)

### Market data

- [Retrieve bars](api-reference/market-data/retrieve-bars.md)
- [Search for contracts](api-reference/market-data/search-contracts.md)
- [Search for contract by id](api-reference/market-data/contract-by-id.md)
- [List available contracts](api-reference/market-data/available-contracts.md)

### Orders

- [Search for orders](api-reference/orders/search.md)
- [Search for open orders](api-reference/orders/search-open.md)
- [Place an order](api-reference/orders/place.md)
- [Cancel an order](api-reference/orders/cancel.md)
- [Modify an order](api-reference/orders/modify.md)

### Positions

- [Search for positions](api-reference/positions/search.md)
- [Close positions](api-reference/positions/close.md)
- [Partially close positions](api-reference/positions/partial-close.md)

### Trades

- [Search for trades](api-reference/trades/search.md)

## Realtime

- [Real-time data overview](realtime/overview.md) — SignalR hubs, subscriptions, events, enums

## Conventions

- All paths below are relative to `https://api.topstepx.com` unless noted.
- Authenticated REST calls use a **JWT session token** obtained from `/api/Auth/loginKey` or `/api/Auth/loginApp`, then passed on subsequent requests (typically `Authorization: Bearer <token>`).
- Responses commonly include `success`, `errorCode`, and `errorMessage` alongside payload fields.

## Testing against PRAC

The repo includes opt-in live integration tests that exercise the real TopstepX / ProjectX REST surface against a **practice** account.

### Required environment

- `TOPSTEPX_INTEGRATION=1`
- `EMAIL`
- `TOPSTEP_API_KEY`
- `PREFERRED_ACCOUNT_ID` must resolve to the practice account you want the tests to use

### Read-only smoke tests

Run the PRAC-safe suite:

```bash
TOPSTEPX_INTEGRATION=1 pytest tests/test_topstepx_integration.py -q
```

These tests cover:

- authentication
- practice-account selection
- broker truth bundles
- positions and order/trade history queries
- historical bar retrieval

### Optional mutating smoke test

If you also want a tiny order lifecycle check on the PRAC account, opt in explicitly:

```bash
TOPSTEPX_INTEGRATION=1 TOPSTEPX_ALLOW_MUTATING_TESTS=1 pytest tests/test_topstepx_integration.py -q
```

That test submits a small off-market limit order on PRAC and cancels it immediately.

### Live startup smoke test

To exercise the full live startup path — CLI `start`, market stream readiness, user-hub connection, runtime `status` / `health`, and graceful shutdown — opt in separately:

```bash
TOPSTEPX_INTEGRATION=1 TOPSTEPX_LIVE_STARTUP_SMOKE=1 pytest tests/test_topstepx_integration.py -q
```

This smoke test starts the real trader process against the PRAC account using a temporary config, waits for live startup events in SQLite, runs the runtime inspection commands through the CLI, and then shuts the process down cleanly.

## Safety

- Do not commit API keys, passwords, or live tokens. Use `.env` locally and keep credentials out of the repo.
