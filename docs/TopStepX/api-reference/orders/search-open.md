# Search for open orders

**Endpoint:** `POST https://api.topstepx.com/api/Order/searchOpen`

**Swagger:** `POST /api/Order/searchOpen`

## Description

Returns **currently open** (working) orders for an account.

## Parameters

| Name | Type | Description | Required | Nullable |
|------|------|-------------|----------|----------|
| `accountId` | integer | Account id | Yes | No |

## Example request

```bash
curl -X POST 'https://api.topstepx.com/api/Order/searchOpen' \
  -H 'accept: text/plain' \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer YOUR_JWT_TOKEN' \
  -d '{"accountId": 212}'
```

## Example success response

```json
{
  "orders": [
    {
      "id": 26970,
      "accountId": 212,
      "contractId": "CON.F.US.EP.M25",
      "creationTimestamp": "2025-04-21T19:45:52.105808+00:00",
      "updateTimestamp": "2025-04-21T19:45:52.105808+00:00",
      "status": 1,
      "type": 4,
      "side": 1,
      "size": 1,
      "limitPrice": null,
      "stopPrice": 5138.0,
      "filledPrice": null
    }
  ],
  "success": true,
  "errorCode": 0,
  "errorMessage": null
}
```

## Notes

- `status: 1` is **Open** in the documented OrderStatus enum — see [Enums](../../realtime/overview.md#enum-definitions).
