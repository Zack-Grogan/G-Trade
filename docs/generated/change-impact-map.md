# Change impact map (generated)

High-impact areas (touching these may require docs/runbook/compliance updates):

- es-hotzone-trader/src/engine/ — trading logic, reconciliation
- es-hotzone-trader/src/execution/ — order execution
- es-hotzone-trader/src/market/ — Topstep client
- es-hotzone-trader/src/bridge/ — telemetry to Railway
- es-hotzone-trader/config/default.yaml — config surface
- railway/ingest/app.py — ingest API and schema
- docs/OPERATOR.md, docs/Compliance-Boundaries.md, docs/runbooks/

See AGENTS.md 'What requires docs updates' and 'What requires approval before editing'.
