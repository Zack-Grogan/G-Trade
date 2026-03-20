# Rate limits

The Gateway API applies rate limits to **authenticated** requests to balance fairness, abuse prevention, and service stability.

## Limits

| Endpoint(s) | Limit |
|-------------|--------|
| `POST /api/History/retrieveBars` | **50** requests per **30** seconds |
| **All other** endpoints | **200** requests per **60** seconds |

## When you exceed limits

The API returns **HTTP `429 Too Many Requests`**.

**What to do:** back off (reduce request frequency), wait briefly, then retry. For heavy bar backfills, batch requests and respect the stricter `retrieveBars` window.

## Related

- [Retrieve bars](../api-reference/market-data/retrieve-bars.md)
