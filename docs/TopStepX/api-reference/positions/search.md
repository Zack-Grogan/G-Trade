# Search for positions

**Endpoint:** `POST https://api.topstepx.com/api/Position/searchOpen`

**Swagger:** `POST /api/Position/searchOpen`

## Description

Returns **open** positions for an account (one row per contract position).

## Parameters

| Name | Type | Description | Required | Nullable |
|------|------|-------------|----------|----------|
| `accountId` | integer | Account id | Yes | No |

## Example request

```bash
curl -X POST 'https://api.topstepx.com/api/Position/searchOpen' \
  -H 'accept: text/plain' \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer YOUR_JWT_TOKEN' \
  -d '{"accountId": 536}'
```

## Example success response

```json
{
  "positions": [
    {
      "id": 6124,
      "accountId": 536,
      "contractId": "CON.F.US.GMET.J25",
      "creationTimestamp": "2025-04-21T19:52:32.175721+00:00",
      "type": 1,
      "size": 2,
      "averagePrice": 1575.75
    }
  ],
  "success": true,
  "errorCode": 0,
  "errorMessage": null
}
```

## Notes

- `type` is `PositionType` — see [Enums](../../realtime/overview.md#enum-definitions) (`Long` / `Short`).
