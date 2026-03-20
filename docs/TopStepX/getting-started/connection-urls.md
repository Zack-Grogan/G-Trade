# Connection URLs (TopStepX)

Use these endpoints for **TopStepX** integrations.

| Surface | URL |
|--------|-----|
| **REST API** | `https://api.topstepx.com` |
| **User hub** (SignalR) | `https://rtc.topstepx.com/hubs/user` |
| **Market hub** (SignalR) | `https://rtc.topstepx.com/hubs/market` |

**Swagger:** `https://api.topstepx.com/swagger/index.html`

## Notes

- REST paths are rooted at `/api/...` (for example `POST https://api.topstepx.com/api/Auth/loginKey`).
- Realtime hubs require a valid JWT; see [Realtime overview](../realtime/overview.md).
