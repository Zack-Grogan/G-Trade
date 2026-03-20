# Retrieve bars

**Endpoint:** `POST https://api.topstepx.com/api/History/retrieveBars`

**Swagger:** `POST /api/History/retrieveBars`

## Description

Retrieves aggregated OHLCV (and related) **bars** for a contract over a time range.

**Limits:**

- Maximum **20,000** bars per request (official docs).
- **Stricter rate limit:** 50 requests / 30 seconds — see [Rate limits](../../getting-started/rate-limits.md).

## Parameters

| Name | Type | Description | Required | Nullable |
|------|------|-------------|----------|----------|
| `contractId` | string | Contract identifier (e.g. `CON.F.US.RTY.Z24`) | Yes | No |
| `live` | boolean | Use live vs sim data subscription | Yes | No |
| `startTime` | datetime | Range start (ISO-8601) | Yes | No |
| `endTime` | datetime | Range end (ISO-8601) | Yes | No |
| `unit` | integer | Aggregation unit: `1` Second, `2` Minute, `3` Hour, `4` Day, `5` Week, `6` Month | Yes | No |
| `unitNumber` | integer | Number of `unit` steps per bar | Yes | No |
| `limit` | integer | Max bars to return | Yes | No |
| `includePartialBar` | boolean | Include current partial bar for the active period | Yes | No |

> **Note:** Some upstream docs list `contractId` as integer; examples use **string** contract ids. Treat as **string** unless Swagger for your environment says otherwise.

## Example request

```bash
curl -X POST 'https://api.topstepx.com/api/History/retrieveBars' \
  -H 'accept: text/plain' \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer YOUR_JWT_TOKEN' \
  -d '{
    "contractId": "CON.F.US.RTY.Z24",
    "live": false,
    "startTime": "2024-12-01T00:00:00Z",
    "endTime": "2024-12-31T21:00:00Z",
    "unit": 3,
    "unitNumber": 1,
    "limit": 7,
    "includePartialBar": false
  }'
```

## Example success response

Bar objects use short keys: `t` time, `o` open, `h` high, `l` low, `c` close, `v` volume.

```json
{
  "bars": [
    {
      "t": "2024-12-20T14:00:00+00:00",
      "o": 2208.1,
      "h": 2217.0,
      "l": 2206.7,
      "c": 2210.1,
      "v": 87
    }
  ],
  "success": true,
  "errorCode": 0,
  "errorMessage": null
}
```
