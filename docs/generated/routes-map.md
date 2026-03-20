# Routes / endpoints map (generated)

## Local operator surface
- No in-process HTTP server. Use CLI: `es-trade status`, `es-trade health`, `es-trade debug`.
- Runtime truth for a separate trader process: SQLite state snapshots in `logs/observability.db` plus `logs/runtime/runtime_status.json`.
