# Placing your first order

You need an **active trading account** and a **contract id** before placing an order. Follow these three steps against **TopStepX** hosts.

**Prerequisite:** [Authenticate](authentication.md) and use `Authorization: Bearer <token>` on each step.

---

## Step 1 — Find your account

Retrieve accounts and pick the `id` you will trade.

**Endpoint:** `POST https://api.topstepx.com/api/Account/search`

**Body:**

```json
{
  "onlyActiveAccounts": true
}
```

**Example:**

```bash
curl -X POST 'https://api.topstepx.com/api/Account/search' \
  -H 'accept: text/plain' \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer YOUR_JWT_TOKEN' \
  -d '{"onlyActiveAccounts": true}'
```

Save **`accountId`** from the response for step 3.

Details: [Search for accounts](../api-reference/account/search.md).

---

## Step 2 — List available contracts

Browse tradable contracts and pick a **`contractId`**.

**Endpoint:** `POST https://api.topstepx.com/api/Contract/available`

**Body (example — sim vs live depends on your subscription):**

```json
{
  "live": false
}
```

**Example:**

```bash
curl -X POST 'https://api.topstepx.com/api/Contract/available' \
  -H 'accept: text/plain' \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer YOUR_JWT_TOKEN' \
  -d '{"live": false}'
```

Save **`contractId`** for step 3.

Details: [List available contracts](../api-reference/market-data/available-contracts.md).

---

## Step 3 — Place the order

**Endpoint:** `POST https://api.topstepx.com/api/Order/place`

**Example body (market order):**

```json
{
  "accountId": 1,
  "contractId": "CON.F.US.BP6.U25",
  "type": 2,
  "side": 1,
  "size": 1
}
```

| Field | Meaning (common values) |
|-------|-------------------------|
| `type` | `1` Limit, `2` Market, `4` Stop, `5` TrailingStop, `6` JoinBid, `7` JoinAsk |
| `side` | `0` Bid (buy), `1` Ask (sell) |

**Example:**

```bash
curl -X POST 'https://api.topstepx.com/api/Order/place' \
  -H 'accept: text/plain' \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer YOUR_JWT_TOKEN' \
  -d '{
    "accountId": 1,
    "contractId": "CON.F.US.BP6.U25",
    "type": 2,
    "side": 1,
    "size": 1
  }'
```

### Example success response

```json
{
  "orderId": 9056,
  "success": true,
  "errorCode": 0,
  "errorMessage": null
}
```

Full parameter list: [Place an order](../api-reference/orders/place.md).

---

## See also

- [Rate limits](rate-limits.md)
- [Enums](../realtime/overview.md#enum-definitions) (order type, side, status)
