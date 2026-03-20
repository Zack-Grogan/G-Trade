# Search for contracts

**Endpoint:** `POST https://api.topstepx.com/api/Contract/search`

**Swagger:** `POST /api/Contract/search`

## Description

Text search for contracts. The API returns **up to 20** contracts per request.

## Parameters

| Name | Type | Description | Required | Nullable |
|------|------|-------------|----------|----------|
| `searchText` | string | Name or fragment to search | Yes | No |
| `live` | boolean | Search using sim vs live data subscription | Yes | No |

## Example request

```bash
curl -X POST 'https://api.topstepx.com/api/Contract/search' \
  -H 'accept: text/plain' \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer YOUR_JWT_TOKEN' \
  -d '{
    "live": false,
    "searchText": "NQ"
  }'
```

## Example success response

```json
{
  "contracts": [
    {
      "id": "CON.F.US.ENQ.U25",
      "name": "NQU5",
      "description": "E-mini NASDAQ-100: September 2025",
      "tickSize": 0.25,
      "tickValue": 5,
      "activeContract": true,
      "symbolId": "F.US.ENQ"
    }
  ],
  "success": true,
  "errorCode": 0,
  "errorMessage": null
}
```

## Notes

- `symbolId` identifies the underlying symbol; `id` is the full contract id used in orders and positions.
