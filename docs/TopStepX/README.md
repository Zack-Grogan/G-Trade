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

## Safety

- Do not commit API keys, passwords, or live tokens. Use `.env` locally and keep credentials out of the repo.
