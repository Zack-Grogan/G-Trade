# List available contracts

**Endpoint:** `POST https://api.topstepx.com/api/Contract/available`

**Swagger:** `POST /api/Contract/available`

## Description

Lists contracts **available to trade** for the authenticated context, filtered by sim vs live data.

## Parameters

| Name | Type | Description | Required | Nullable |
|------|------|-------------|----------|----------|
| `live` | boolean | If true, use live subscription; if false, sim | Yes | No |

## Example request

```bash
curl -X POST 'https://api.topstepx.com/api/Contract/available' \
  -H 'accept: text/plain' \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer YOUR_JWT_TOKEN' \
  -d '{"live": true}'
```

## Example success response (truncated)

```json
{
  "contracts": [
    {
      "id": "CON.F.US.BP6.U25",
      "name": "6BU5",
      "description": "British Pound (Globex): September 2025",
      "tickSize": 0.0001,
      "tickValue": 6.25,
      "activeContract": true,
      "symbolId": "F.US.BP6"
    }
  ],
  "success": true,
  "errorCode": 0,
  "errorMessage": null
}
```

## Notes

- Use this list to populate contract pickers or to resolve ids before [placing orders](../orders/place.md).
