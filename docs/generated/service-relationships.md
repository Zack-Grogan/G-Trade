# Service relationships (generated)

```
Mac (es-hotzone-trader)
  CLI → engine → execution, market (Topstep)
  engine → observability (SQLite)
  bridge ← debug server, observability → outbox → HTTPS → Railway ingest

Railway
  ingest → Postgres
  analytics ← Postgres (read-only)
  mcp ← analytics API (read-only)
  web ← analytics API (read-only)
  Cursor/IDE → mcp (MCP)
```

Data flow: Mac → Railway only. No execution or broker on Railway.
