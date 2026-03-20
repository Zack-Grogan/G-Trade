# Search for trades

**Endpoint:** `POST https://api.topstepx.com/api/Trade/search`

**Swagger:** `POST /api/Trade/search`

## Description

Returns **filled** trades for an account within a time range. Used for P&amp;L, fills, and reconciliation.

## Parameters

| Name | Type | Description | Required | Nullable |
|------|------|-------------|----------|----------|
| `accountId` | integer | Account id | Yes | No |
| `startTimestamp` | datetime | Range start (ISO-8601) | Yes | No |
| `endTimestamp` | datetime | Range end (ISO-8601) | Optional | Yes |

## Example request

```bash
curl -X POST 'https://api.topstepx.com/api/Trade/search' \
  -H 'accept: text/plain' \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer YOUR_JWT_TOKEN' \
  -d '{
    "accountId": 203,
    "startTimestamp": "2025-01-20T15:47:39.882Z",
    "endTimestamp": "2025-01-30T15:47:39.882Z"
  }'
```

## Example success response

```json
{
  "trades": [
    {
      "id": 8604,
      "accountId": 203,
      "contractId": "CON.F.US.EP.H25",
      "creationTimestamp": "2025-01-21T16:13:52.523293+00:00",
      "price": 6065.25,
      "profitAndLoss": 50.0,
      "fees": 1.4,
      "side": 1,
      "size": 1,
      "voided": false,
      "orderId": 14328
    },
    {
      "id": 8603,
      "accountId": 203,
      "contractId": "CON.F.US.EP.H25",
      "creationTimestamp": "2025-01-21T16:13:04.142302+00:00",
      "price": 6064.25,
      "profitAndLoss": null,
      "fees": 1.4,
      "side": 0,
      "size": 1,
      "voided": false,
      "orderId": 14326
    }
  ],
  "success": true,
  "errorCode": 0,
  "errorMessage": null
}
```

## Notes

- **`profitAndLoss: null`** may indicate a **half-turn** leg (opening side of a round trip); upstream docs call this out explicitly.
- `voided` indicates whether the trade was voided.
