# Routes / endpoints map (generated)

## railway/ingest
- POST /ingest/state
- POST /ingest/events
- POST /ingest/trades
- GET /health

## railway/analytics
- GET /runs
- GET /runs/{run_id}
- GET /runs/{run_id}/events
- GET /runs/{run_id}/trades
- GET /analytics/summary
- GET /health

## railway/mcp
- POST /mcp (JSON-RPC)
- GET /mcp (metadata)
- GET /health

## railway/web
- Next.js app; calls analytics API only.

## es-hotzone-trader (local debug server)
- GET /health
- GET /debug (state snapshot)
