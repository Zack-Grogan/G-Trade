# Environment variables

Reference for the active local trader stack. Copy from `.env.example` and set only what you need locally.

| Variable | Where used | Required |
|----------|------------|----------|
| `TOPSTEP_USERNAME` | local broker auth | if not stored elsewhere |
| `TOPSTEP_API_KEY` / related broker env | local broker auth | if required by your setup |
| `PREFERRED_ACCOUNT_ID` | **only** runtime account selector (practice or funded live); must match a tradable account id returned by the broker | optional but recommended for an explicit cut |
| `LIVE_ACCOUNT_ID` | local reference only (copy/paste convenience); **not** read by the runtime | optional |
| `PRACTICE_ACCOUNT_ID` | local reference only (copy/paste convenience); **not** read by the runtime | optional |
| `LOCAL_DURABILITY_DB_PATH` | SQLite override | optional |
Market-hours entry guard is configured in `config/default.yaml` under `strategy.*`:
- `market_hours_guard_enabled`
- `market_hours_timezone`
- `market_hours_daily_maintenance_start` / `market_hours_daily_maintenance_end`
- `market_hours_weekend_close_day` / `market_hours_weekend_close_time`
- `market_hours_weekend_open_day` / `market_hours_weekend_open_time`
- `market_hours_holiday_dates`

Local-only config files remain uncommitted:

- `.env`
- `.cursor/mcp.json`
- `.codex/config.toml`

Committed examples:

- `.env.example`
- `.cursor/mcp.example.json`
- `.codex/config.example.toml`
