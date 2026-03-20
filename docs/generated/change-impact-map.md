# Change impact map (generated)

High-impact areas (touching these may require docs/runbook/compliance updates):

- src/engine/ — trading logic, reconciliation
- src/execution/ — order execution
- src/market/ — Topstep client
- src/runtime/ — in-process trading state and CLI/SQLite inspection helpers
- docs/archive/railway-sunset/ — retired bridge/outbox history only
- config/default.yaml — config surface
- docs/OPERATOR.md, docs/Compliance-Boundaries.md, docs/runbooks/

See AGENTS.md 'What requires docs updates' and 'What requires approval before editing'.
