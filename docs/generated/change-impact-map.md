# Change impact map (generated)

High-impact areas (touching these may require docs/runbook/compliance updates):

- es-hotzone-trader/src/engine/ — trading logic, reconciliation
- es-hotzone-trader/src/execution/ — order execution
- es-hotzone-trader/src/market/ — Topstep client
- es-hotzone-trader/src/server/ — local Flask console and health/debug surfaces
- es-hotzone-trader/src/bridge/ — legacy bridge code retained for historical recovery only
- es-hotzone-trader/config/default.yaml — config surface
- docs/OPERATOR.md, docs/Compliance-Boundaries.md, docs/runbooks/

See AGENTS.md 'What requires docs updates' and 'What requires approval before editing'.
