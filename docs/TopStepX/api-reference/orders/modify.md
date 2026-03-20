# Modify an order

**Endpoint:** `POST https://api.topstepx.com/api/Order/modify`

**Swagger:** `POST /api/Order/modify`

## Description

Modifies an **open** order (size, limit, stop, or trail fields as applicable).

## Parameters

| Name | Type | Description | Required | Nullable |
|------|------|-------------|----------|----------|
| `accountId` | integer | Account id | Yes | No |
| `orderId` | integer | Order id | Yes | No |
| `size` | integer | New size | Optional | Yes |
| `limitPrice` | decimal | New limit price | Optional | Yes |
| `stopPrice` | decimal | New stop price | Optional | Yes |
| `trailPrice` | decimal | New trail price | Optional | Yes |

## Example request

```bash
curl -X POST 'https://api.topstepx.com/api/Order/modify' \
  -H 'accept: text/plain' \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer YOUR_JWT_TOKEN' \
  -d '{
    "accountId": 465,
    "orderId": 26974,
    "size": 1,
    "limitPrice": null,
    "stopPrice": 1604,
    "trailPrice": null
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
