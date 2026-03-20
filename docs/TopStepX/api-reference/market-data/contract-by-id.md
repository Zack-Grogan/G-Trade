# Search for contract by id

**Endpoint:** `POST https://api.topstepx.com/api/Contract/searchById`

**Swagger:** `POST /api/Contract/searchById`

## Description

Returns metadata for a **single** contract when you already know its `contractId`.

## Parameters

| Name | Type | Description | Required | Nullable |
|------|------|-------------|----------|----------|
| `contractId` | string | Full contract id (e.g. `CON.F.US.ENQ.H25`) | Yes | No |

## Example request

```bash
curl -X POST 'https://api.topstepx.com/api/Contract/searchById' \
  -H 'accept: text/plain' \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer YOUR_JWT_TOKEN' \
  -d '{"contractId": "CON.F.US.ENQ.H25"}'
```

## Example success response

```json
{
  "contract": {
    "id": "CON.F.US.ENQ.H25",
    "name": "NQH5",
    "description": "E-mini NASDAQ-100: March 2025",
    "tickSize": 0.25,
    "tickValue": 5,
    "activeContract": false,
    "symbolId": "F.US.ENQ"
  },
  "success": true,
  "errorCode": 0,
  "errorMessage": null
}
```
