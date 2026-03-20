# Partially close positions

**Endpoint:** `POST https://api.topstepx.com/api/Position/partialCloseContract`

**Swagger:** `POST /api/Position/partialCloseContract`

## Description

Reduces an open position by a **quantity** (`size`) for a contract.

## Parameters

| Name | Type | Description | Required | Nullable |
|------|------|-------------|----------|----------|
| `accountId` | integer | Account id | Yes | No |
| `contractId` | string | Contract id | Yes | No |
| `size` | integer | Contracts to close | Yes | No |

## Example request

```bash
curl -X POST 'https://api.topstepx.com/api/Position/partialCloseContract' \
  -H 'accept: text/plain' \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer YOUR_JWT_TOKEN' \
  -d '{
    "accountId": 536,
    "contractId": "CON.F.US.GMET.J25",
    "size": 1
  }'
```

## Example success response

```json
{
  "success": true,
  "errorCode": 0,
  "errorMessage": null
}
```
