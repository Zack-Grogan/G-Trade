# Search for accounts

**Endpoint:** `POST https://api.topstepx.com/api/Account/search`

**Swagger:** [Account_SearchAccounts](https://api.topstepx.com/swagger/index.html) — `POST /api/Account/search`

## Description

Returns accounts visible to the authenticated user. Use `onlyActiveAccounts` to restrict to active accounts.

## Parameters

| Name | Type | Description | Required | Nullable |
|------|------|-------------|----------|----------|
| `onlyActiveAccounts` | boolean | If true, return only active accounts | Yes | No |

## Example request

```bash
curl -X POST 'https://api.topstepx.com/api/Account/search' \
  -H 'accept: text/plain' \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer YOUR_JWT_TOKEN' \
  -d '{"onlyActiveAccounts": true}'
```

## Example success response

```json
{
  "accounts": [
    {
      "id": 1,
      "name": "TEST_ACCOUNT_1",
      "balance": 50000,
      "canTrade": true,
      "isVisible": true
    }
  ],
  "success": true,
  "errorCode": 0,
  "errorMessage": null
}
```

## Notes

- Use the returned `id` as `accountId` in orders, positions, and searches.
- Account fields may include balance and visibility flags; exact schema is authoritative in Swagger.
