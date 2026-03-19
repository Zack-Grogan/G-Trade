# Environment variables

Reference for the active local trader stack. Copy from `.env.example` and set only what you need locally.

| Variable | Where used | Required |
|----------|------------|----------|
| `TOPSTEP_USERNAME` | local broker auth | if not stored elsewhere |
| `TOPSTEP_API_KEY` / related broker env | local broker auth | if required by your setup |
| `PREFERRED_ACCOUNT_ID` | active practice/live account selection | optional |
| `LOCAL_DURABILITY_DB_PATH` | SQLite override | optional |
| `TRADER_HEALTH_PORT` | local `/health` port override | optional |
| `TRADER_CONSOLE_PORT` | local Flask port override | optional |
| `OPENVIKING_CONFIG_FILE` | local OpenViking use | optional |

Local-only config files remain uncommitted:

- `.env`
- `.cursor/mcp.json`
- `.codex/config.toml`

Committed examples:

- `.env.example`
- `.cursor/mcp.example.json`
- `.codex/config.example.toml`
