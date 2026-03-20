# Place an order

**Endpoint:** `POST https://api.topstepx.com/api/Order/place`

**Swagger:** `POST /api/Order/place`

## Description

Submits a new order (limit, market, stop, trailing, join bid/ask) with optional bracket legs.

## Parameters

| Name | Type | Description | Required | Nullable |
|------|------|-------------|----------|----------|
| `accountId` | integer | Account id | Yes | No |
| `contractId` | string | Contract id | Yes | No |
| `type` | integer | Order type — see below | Yes | No |
| `side` | integer | `0` Bid (buy), `1` Ask (sell) | Yes | No |
| `size` | integer | Order size | Yes | No |
| `limitPrice` | decimal | Limit price (if applicable) | Optional | Yes |
| `stopPrice` | decimal | Stop price (if applicable) | Optional | Yes |
| `trailPrice` | decimal | Trail price (if applicable) | Optional | Yes |
| `customTag` | string | Optional tag; **must be unique** per account | Optional | Yes |
| `stopLossBracket` | object | `{ "ticks": int, "type": int }` — see bracket types | Optional | Yes |
| `takeProfitBracket` | object | `{ "ticks": int, "type": int }` | Optional | Yes |

### Order `type` values

| Value | Meaning |
|-------|---------|
| `1` | Limit |
| `2` | Market |
| `4` | Stop |
| `5` | TrailingStop |
| `6` | JoinBid |
| `7` | JoinAsk |

Bracket `type` uses the same `OrderType` values as above.

## Example request

```bash
curl -X POST 'https://api.topstepx.com/api/Order/place' \
  -H 'accept: text/plain' \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer YOUR_JWT_TOKEN' \
  -d '{
    "accountId": 465,
    "contractId": "CON.F.US.DA6.M25",
    "type": 2,
    "side": 1,
    "size": 1,
    "limitPrice": null,
    "stopPrice": null,
    "trailPrice": null,
    "customTag": null,
    "stopLossBracket": { "ticks": 10, "type": 1 },
    "takeProfitBracket": { "ticks": 20, "type": 1 }
  }'
```

## Example success response

```json
{
  "orderId": 9056,
  "success": true,
  "errorCode": 0,
  "errorMessage": null
}
```

## Notes

- For a minimal market order, only `accountId`, `contractId`, `type`, `side`, and `size` are required.
- See [First order](../../getting-started/first-order.md) for a short walkthrough.
