# Real-time data overview

The **ProjectX Real Time API** uses **SignalR** over **WebSockets** for push updates. There are **two hubs**:

| Hub | URL (TopStepX) | Purpose |
|-----|----------------|--------|
| **User** | `https://rtc.topstepx.com/hubs/user` | Accounts, orders, positions, trades for the user |
| **Market** | `https://rtc.topstepx.com/hubs/market` | Quotes, depth (DOM), market trades |

Use the **same JWT** you obtain from [Authentication](../getting-started/authentication.md) for REST.

## What is SignalR?

SignalR is Microsoft’s real-time framework; it negotiates WebSocket (or fallback transports) and handles reconnects. Official intro: [Introduction to SignalR](https://learn.microsoft.com/en-us/aspnet/signalr/overview/getting-started/introduction-to-signalr).

---

## User hub — connection and subscriptions

Typical pattern (Node.js with `@microsoft/signalr`):

- Build `HubConnection` to **`https://rtc.topstepx.com/hubs/user`**
- Use **WebSockets** and pass the JWT via `accessTokenFactory` (and/or query string as required by your client)
- On connect, **invoke** subscription methods; **re-subscribe** after reconnect

**Example (illustrative):**

```javascript
const { HubConnectionBuilder, HttpTransportType } = require('@microsoft/signalr');

function setupUserHub() {
  const JWT_TOKEN = 'your_bearer_token';
  const SELECTED_ACCOUNT_ID = 123;

  const userHubUrl = 'https://rtc.topstepx.com/hubs/user';

  const rtcConnection = new HubConnectionBuilder()
    .withUrl(userHubUrl, {
      skipNegotiation: true,
      transport: HttpTransportType.WebSockets,
      accessTokenFactory: () => JWT_TOKEN,
      timeout: 10000,
    })
    .withAutomaticReconnect()
    .build();

  rtcConnection
    .start()
    .then(() => {
      const subscribe = () => {
        rtcConnection.invoke('SubscribeAccounts');
        rtcConnection.invoke('SubscribeOrders', SELECTED_ACCOUNT_ID);
        rtcConnection.invoke('SubscribePositions', SELECTED_ACCOUNT_ID);
        rtcConnection.invoke('SubscribeTrades', SELECTED_ACCOUNT_ID);
      };

      const unsubscribe = () => {
        rtcConnection.invoke('UnsubscribeAccounts');
        rtcConnection.invoke('UnsubscribeOrders', SELECTED_ACCOUNT_ID);
        rtcConnection.invoke('UnsubscribePositions', SELECTED_ACCOUNT_ID);
        rtcConnection.invoke('UnsubscribeTrades', SELECTED_ACCOUNT_ID);
      };

      rtcConnection.on('GatewayUserAccount', (data) => {
        console.log('Account update', data);
      });
      rtcConnection.on('GatewayUserOrder', (data) => {
        console.log('Order update', data);
      });
      rtcConnection.on('GatewayUserPosition', (data) => {
        console.log('Position update', data);
      });
      rtcConnection.on('GatewayUserTrade', (data) => {
        console.log('Trade update', data);
      });

      subscribe();

      rtcConnection.onreconnected(() => {
        console.log('RTC reconnected');
        subscribe();
      });
    })
    .catch((err) => console.error(err));
}
```

**Invoke methods (documented):**

| Invoke | Purpose |
|--------|---------|
| `SubscribeAccounts` | Account stream |
| `SubscribeOrders(accountId)` | Orders for account |
| `SubscribePositions(accountId)` | Positions for account |
| `SubscribeTrades(accountId)` | Trades for account |
| `UnsubscribeAccounts` | Stop account stream |
| `UnsubscribeOrders(accountId)` | … |
| `UnsubscribePositions(accountId)` | … |
| `UnsubscribeTrades(accountId)` | … |

**Events (client `on`):**

| Event | Payload summary |
|-------|-----------------|
| `GatewayUserAccount` | Account snapshot/update |
| `GatewayUserOrder` | Order update |
| `GatewayUserPosition` | Position update |
| `GatewayUserTrade` | Trade fill update |

### User hub — example payloads

**GatewayUserAccount**

```json
{
  "id": 123,
  "name": "Main Trading Account",
  "balance": 10000.5,
  "canTrade": true,
  "isVisible": true,
  "simulated": false
}
```

| Field | Type | Description |
|-------|------|-------------|
| `id` | int | Account id |
| `name` | string | Display name |
| `balance` | number | Balance |
| `canTrade` | bool | Trading allowed |
| `isVisible` | bool | UI visibility |
| `simulated` | bool | Sim vs live |

**GatewayUserPosition**

```json
{
  "id": 456,
  "accountId": 123,
  "contractId": "CON.F.US.EP.U25",
  "creationTimestamp": "2024-07-21T13:45:00Z",
  "type": 1,
  "size": 2,
  "averagePrice": 2100.25
}
```

**GatewayUserOrder**

```json
{
  "id": 789,
  "accountId": 123,
  "contractId": "CON.F.US.EP.U25",
  "symbolId": "F.US.EP",
  "creationTimestamp": "2024-07-21T13:45:00Z",
  "updateTimestamp": "2024-07-21T13:46:00Z",
  "status": 1,
  "type": 1,
  "side": 0,
  "size": 1,
  "limitPrice": 2100.5,
  "stopPrice": null,
  "fillVolume": 0,
  "filledPrice": null,
  "customTag": "strategy-1"
}
```

**GatewayUserTrade**

```json
{
  "id": 101112,
  "accountId": 123,
  "contractId": "CON.F.US.EP.U25",
  "creationTimestamp": "2024-07-21T13:47:00Z",
  "price": 2100.75,
  "profitAndLoss": 50.25,
  "fees": 2.5,
  "side": 0,
  "size": 1,
  "voided": false,
  "orderId": 789
}
```

---

## Market hub — events

Connect to **`https://rtc.topstepx.com/hubs/market`** using the same SignalR patterns. Documented event types include:

### GatewayQuote

```json
{
  "symbol": "F.US.EP",
  "symbolName": "/ES",
  "lastPrice": 2100.25,
  "bestBid": 2100.0,
  "bestAsk": 2100.5,
  "change": 25.5,
  "changePercent": 0.14,
  "open": 2090.0,
  "high": 2110.0,
  "low": 2080.0,
  "volume": 12000,
  "lastUpdated": "2024-07-21T13:45:00Z",
  "timestamp": "2024-07-21T13:45:00Z"
}
```

| Field | Description |
|-------|-------------|
| `symbol` | Symbol id |
| `symbolName` | Friendly name (may be unused) |
| `lastPrice` / `bestBid` / `bestAsk` | Top of book |
| `change` / `changePercent` | Session change |
| `open` / `high` / `low` | Session OHLC context |
| `volume` | Volume |
| `lastUpdated` / `timestamp` | Times |

### GatewayDepth (DOM)

```json
{
  "timestamp": "2024-07-21T13:45:00Z",
  "type": 1,
  "price": 2100.0,
  "volume": 10,
  "currentVolume": 5
}
```

`type` uses `DomType` — see [Enum definitions](#enum-definitions).

### GatewayTrade (tape)

```json
{
  "symbolId": "F.US.EP",
  "price": 2100.25,
  "timestamp": "2024-07-21T13:45:00Z",
  "type": 0,
  "volume": 2
}
```

---

## Enum definitions

Values below match the ProjectX Gateway documentation (C#-style names for reference).

### DomType

```
Unknown      = 0
Ask          = 1
Bid          = 2
BestAsk      = 3
BestBid      = 4
Trade        = 5
Reset        = 6
Low          = 7
High         = 8
NewBestBid   = 9
NewBestAsk   = 10
Fill         = 11
```

### OrderSide

```
Bid = 0
Ask = 1
```

### OrderType

```
Unknown       = 0
Limit         = 1
Market        = 2
StopLimit     = 3
Stop          = 4
TrailingStop  = 5
JoinBid       = 6
JoinAsk       = 7
```

### OrderStatus

```
None      = 0
Open      = 1
Filled    = 2
Cancelled = 3
Expired   = 4
Rejected  = 5
Pending   = 6
```

### TradeLogType

```
Buy  = 0
Sell = 1
```

### PositionType

```
Undefined = 0
Long      = 1
Short     = 2
```

---

## Operational notes

- **JWT** must be valid; refresh via `POST /api/Auth/validate` before long-lived sessions.
- On **reconnect**, repeat **Subscribe\*** invocations so streams resume.
- Market hub subscription method names for your build may be documented in Swagger or upstream examples; align with the version you run.

## See also

- [Connection URLs](../getting-started/connection-urls.md)
- [Rate limits](../getting-started/rate-limits.md)
