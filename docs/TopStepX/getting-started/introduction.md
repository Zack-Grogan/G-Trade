# Introduction

## What this API is

The **ProjectX Gateway API** is a REST API for managing prop-firm trader operations: accounts, contracts, orders, positions, trades, and historical bars. **TopStepX** exposes the same gateway shape as other ProjectX-backed platforms; only the **hostnames** differ.

## What you need

- **HTTP client** — cURL, Postman, or your language’s HTTP library.
- **REST basics** — JSON request bodies, `POST` endpoints, JSON responses.
- **Credentials** — from your firm (Topstep): API key and username for API-key login, or application credentials where applicable.

## Authentication model

The API uses **JSON Web Tokens (JWT)**. You obtain a **session token** via `POST /api/Auth/loginKey` or `POST /api/Auth/loginApp`, then send that token on subsequent requests until it expires (see [Authentication](authentication.md)).

## Realtime

Market and account updates are delivered over **SignalR** (WebSockets) on two hubs. See [Real-time data overview](../realtime/overview.md).

## Platform note

The public ProjectX docs may show **The Futures Desk** example URLs (`api.thefuturesdesk.projectx.com`). For **TopStepX**, use **`https://api.topstepx.com`** and the RTC hosts under **`https://rtc.topstepx.com`**. The **path and semantics** are the same.

## Next steps

1. [Connection URLs](connection-urls.md)
2. [Authentication](authentication.md)
3. [Placing your first order](first-order.md)
