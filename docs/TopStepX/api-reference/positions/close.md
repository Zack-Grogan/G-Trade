# Close positions

**Endpoint:** `POST https://api.topstepx.com/api/Position/closeContract`

**Swagger:** `POST /api/Position/closeContract`

## Description

Closes the **entire** position for a given contract on an account (flatten).

## Parameters

| Name | Type | Description | Required | Nullable |
|------|------|-------------|----------|----------|
| `accountId` | integer | Account id | Yes | No |
| `contractId` | string | Contract id | Yes | No |

## Example request

```bash
curl -X POST 'https://api.topstepx.com/api/Position/closeContract' \
  -H 'accept: text/plain' \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer YOUR_JWT_TOKEN' \
  -d '{
    "accountId": 536,
    "contractId": "CON.F.US.GMET.J25"
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

## Notes

- Use [Partial close](partial-close.md) to reduce size without closing fully.
