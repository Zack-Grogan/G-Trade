# Cancel an order

**Endpoint:** `POST https://api.topstepx.com/api/Order/cancel`

**Swagger:** `POST /api/Order/cancel`

## Description

Cancels an **open** order by id.

## Parameters

| Name | Type | Description | Required | Nullable |
|------|------|-------------|----------|----------|
| `accountId` | integer | Account id | Yes | No |
| `orderId` | integer | Order id to cancel | Yes | No |

## Example request

```bash
curl -X POST 'https://api.topstepx.com/api/Order/cancel' \
  -H 'accept: text/plain' \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer YOUR_JWT_TOKEN' \
  -d '{
    "accountId": 465,
    "orderId": 26974
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
