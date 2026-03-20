# Search for orders

**Endpoint:** `POST https://api.topstepx.com/api/Order/search`

**Swagger:** `POST /api/Order/search`

## Description

Returns **historical** orders for an account within a timestamp range.

## Parameters

| Name | Type | Description | Required | Nullable |
|------|------|-------------|----------|----------|
| `accountId` | integer | Account id | Yes | No |
| `startTimestamp` | datetime | Range start (ISO-8601) | Yes | No |
| `endTimestamp` | datetime | Range end (ISO-8601) | Optional | Yes |

## Example request

```bash
curl -X POST 'https://api.topstepx.com/api/Order/search' \
  -H 'accept: text/plain' \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer YOUR_JWT_TOKEN' \
  -d '{
    "accountId": 704,
    "startTimestamp": "2025-07-18T21:00:01.268009+00:00",
    "endTimestamp": "2025-07-18T21:00:01.278009+00:00"
  }'
```

## Example success response

```json
{
  "orders": [
    {
      "id": 36598,
      "accountId": 704,
      "contractId": "CON.F.US.EP.U25",
      "symbolId": "F.US.EP",
      "creationTimestamp": "2025-07-18T21:00:01.268009+00:00",
      "updateTimestamp": "2025-07-18T21:00:01.268009+00:00",
      "status": 2,
      "type": 2,
      "side": 0,
      "size": 1,
      "limitPrice": null,
      "stopPrice": null,
      "fillVolume": 1,
      "filledPrice": 6335.25,
      "customTag": null
    }
  ],
  "success": true,
  "errorCode": 0,
  "errorMessage": null
}
```

## Notes

- `status`, `type`, `side` are integer enums — see [Enums](../../realtime/overview.md#enum-definitions).
